
import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.7.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_ANON_KEY') ?? ''
);

interface LandingAIResponse {
  predictions: Array<{
    text: string;
    confidence: number;
    bounding_box: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  raw_text: string;
  structured_data: any;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const formData = await req.formData();
    const imageFile = formData.get('image') as File;
    const sessionId = formData.get('sessionId') as string;
    const fileName = formData.get('fileName') as string;
    const fileType = formData.get('fileType') as string; // 'old' or 'new'

    if (!imageFile || !sessionId || !fileName) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`Processing ${fileType} file: ${fileName}`);

    // رفع الصورة إلى Supabase Storage
    const fileBuffer = await imageFile.arrayBuffer();
    const filePath = `${sessionId}/${fileType}/${fileName}`;
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('comparison-files')
      .upload(filePath, fileBuffer, {
        contentType: imageFile.type,
        upsert: true
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      return new Response(
        JSON.stringify({ error: 'Failed to upload file' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // معالجة الصورة باستخدام Landing.AI
    const landingAIKey = Deno.env.get('LANDING_AI_API_KEY');
    const landingAIFormData = new FormData();
    landingAIFormData.append('file', new Blob([fileBuffer], { type: imageFile.type }));

    const landingAIResponse = await fetch('https://predict.app.landing.ai/inference/v1/predict?endpoint_id=your-endpoint-id', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${landingAIKey}`,
      },
      body: landingAIFormData
    });

    const landingAIResult: LandingAIResponse = await landingAIResponse.json();

    // استخراج النص المنظم
    const extractedText = landingAIResult.raw_text || landingAIResult.predictions.map(p => p.text).join('\n');
    
    // إنشاء JSON و MD files
    const jsonData = {
      fileName,
      fileType,
      extractedText,
      predictions: landingAIResult.predictions,
      structuredData: landingAIResult.structured_data,
      processedAt: new Date().toISOString(),
      confidence: landingAIResult.predictions.reduce((acc, p) => acc + p.confidence, 0) / landingAIResult.predictions.length
    };

    const mdContent = `# ${fileName} - استخراج النص
    
## معلومات الملف
- **اسم الملف**: ${fileName}
- **نوع الملف**: ${fileType === 'old' ? 'الكتاب القديم' : 'الكتاب الجديد'}
- **تاريخ المعالجة**: ${new Date().toLocaleString('ar-EG')}
- **معدل الثقة**: ${(jsonData.confidence * 100).toFixed(2)}%

## النص المستخرج
${extractedText}

## البيانات المنظمة
${JSON.stringify(landingAIResult.structured_data, null, 2)}
`;

    // حفظ ملفات JSON و MD
    const jsonFileName = `${fileName.replace(/\.[^/.]+$/, "")}.json`;
    const mdFileName = `${fileName.replace(/\.[^/.]+$/, "")}.md`;

    await Promise.all([
      supabase.storage
        .from('comparison-files')
        .upload(`${sessionId}/${fileType}/json/${jsonFileName}`, JSON.stringify(jsonData, null, 2), {
          contentType: 'application/json',
          upsert: true
        }),
      supabase.storage
        .from('comparison-files')
        .upload(`${sessionId}/${fileType}/md/${mdFileName}`, mdContent, {
          contentType: 'text/markdown',
          upsert: true
        })
    ]);

    // حفظ النتائج في قاعدة البيانات
    const { data: fileUrl } = supabase.storage
      .from('comparison-files')
      .getPublicUrl(filePath);

    const comparisonData = {
      session_id: sessionId,
      [`${fileType}_file_name`]: fileName,
      [`${fileType}_file_url`]: fileUrl.publicUrl,
      [`extracted_text_${fileType}`]: extractedText,
      status: 'completed'
    };

    // البحث عن سجل موجود أو إنشاء جديد
    const { data: existingRecord } = await supabase
      .from('file_comparisons')
      .select('*')
      .eq('session_id', sessionId)
      .eq(`${fileType}_file_name`, fileName)
      .single();

    if (existingRecord) {
      await supabase
        .from('file_comparisons')
        .update(comparisonData)
        .eq('id', existingRecord.id);
    } else {
      await supabase
        .from('file_comparisons')
        .insert(comparisonData);
    }

    return new Response(
      JSON.stringify({
        success: true,
        extractedText,
        jsonData,
        confidence: jsonData.confidence,
        fileUrl: fileUrl.publicUrl
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Processing error:', error);
    return new Response(
      JSON.stringify({ error: 'Processing failed', details: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
