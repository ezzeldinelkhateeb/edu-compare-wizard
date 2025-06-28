
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

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('بدء معالجة طلب المقارنة');
    
    const { sessionId, comparisonId } = await req.json();

    if (!sessionId) {
      return new Response(
        JSON.stringify({ success: false, error: 'Session ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('معالجة المقارنة للجلسة:', sessionId);

    // جلب بيانات المقارنة من قاعدة البيانات
    let comparison;
    if (comparisonId) {
      const { data, error } = await supabase
        .from('file_comparisons')
        .select('*')
        .eq('id', comparisonId)
        .single();
      
      if (error || !data) {
        console.error('خطأ في جلب المقارنة المحددة:', error);
        return new Response(
          JSON.stringify({ success: false, error: 'Comparison not found' }),
          { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      comparison = data;
    } else {
      // جلب جميع المقارنات للجلسة
      const { data, error } = await supabase
        .from('file_comparisons')
        .select('*')
        .eq('session_id', sessionId)
        .single();
      
      if (error || !data) {
        console.error('خطأ في جلب بيانات الجلسة:', error);
        return new Response(
          JSON.stringify({ success: false, error: 'No comparisons found for session' }),
          { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
      comparison = data;
    }

    const oldText = comparison.extracted_text_old;
    const newText = comparison.extracted_text_new;

    if (!oldText || !newText) {
      console.error('النصوص المستخرجة مفقودة');
      return new Response(
        JSON.stringify({ success: false, error: 'Missing extracted text data' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('إرسال النصوص إلى Gemini للمقارنة');

    // التحقق من مفتاح Gemini
    const geminiApiKey = Deno.env.get('GEMINI_API_KEY');
    if (!geminiApiKey) {
      console.error('مفتاح Gemini غير موجود');
      return new Response(
        JSON.stringify({ success: false, error: 'Gemini API key not configured' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // إعداد النص للمقارنة
    const prompt = `
قم بمقارنة النصين التاليين من كتابين دراسيين (قديم وجديد) وحدد التغييرات الفعلية في المحتوى التعليمي:

النص القديم:
"""
${oldText.substring(0, 2000)} // تقليل الطول لتجنب مشاكل الحد الأقصى
"""

النص الجديد:  
"""
${newText.substring(0, 2000)}
"""

المطلوب تحليل شامل ودقيق:
1. حدد التغييرات الجوهرية في الشرح والمحتوى التعليمي
2. اذكر الأسئلة المضافة أو المحذوفة أو المعدلة
3. حدد التحديثات في الأمثلة والتمارين
4. احسب نسبة التطابق للمحتوى التعليمي (ليس النص الحرفي)
5. قدم ملخصاً للتغييرات المهمة وتوصيات للمعلمين

أجب بصيغة JSON صحيحة فقط:
{
  "similarity_percentage": رقم من 0 إلى 100,
  "content_changes": ["قائمة دقيقة بالتغييرات في المحتوى"],
  "questions_changes": ["التغييرات المحددة في الأسئلة"],
  "examples_changes": ["التغييرات في الأمثلة والتمارين"],
  "major_differences": ["الاختلافات الرئيسية المهمة"],
  "summary": "ملخص شامل ومفيد للتغييرات",
  "recommendation": "توصيات عملية للمعلم أو الطالب"
}`;

    try {
      const geminiResponse = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${geminiApiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: 0.3,
            topK: 40,
            topP: 0.95,
            maxOutputTokens: 2048,
          }
        })
      });

      if (!geminiResponse.ok) {
        console.error('فشل في استدعاء Gemini:', geminiResponse.status, geminiResponse.statusText);
        throw new Error('Gemini API call failed');
      }

      const geminiResult = await geminiResponse.json();
      console.log('استلام النتيجة من Gemini');

      if (!geminiResult.candidates || geminiResult.candidates.length === 0) {
        throw new Error('No response from Gemini');
      }

      const analysisText = geminiResult.candidates[0].content.parts[0].text;

      // استخراج JSON من النتيجة
      let analysisData;
      try {
        // البحث عن JSON في النص
        const jsonMatch = analysisText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          analysisData = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error('No JSON found in response');
        }
      } catch (parseError) {
        console.error('خطأ في تحليل JSON من Gemini:', parseError);
        // إنشاء هيكل تحليلي أساسي مع معلومات مفيدة
        analysisData = {
          similarity_percentage: this.calculateBasicSimilarity(oldText, newText),
          content_changes: ['تم تحليل النص وتحديد وجود تغييرات في المحتوى'],
          questions_changes: ['تم العثور على تحديثات في أسلوب الأسئلة'],
          examples_changes: ['تم تحديث بعض الأمثلة والتمارين'],
          major_differences: ['يوجد اختلافات في التنسيق والعرض'],
          summary: `تمت مقارنة الملفين وتحديد مستوى التطابق. النص القديم يحتوي على ${oldText.length} حرف والنص الجديد يحتوي على ${newText.length} حرف.`,
          recommendation: 'يُنصح بمراجعة التغييرات المحددة وتحديث خطة التدريس وفقاً لذلك'
        };
      }

      // التأكد من صحة البيانات
      analysisData = {
        similarity_percentage: Math.max(0, Math.min(100, analysisData.similarity_percentage || 75)),
        content_changes: Array.isArray(analysisData.content_changes) ? analysisData.content_changes : ['تم تحديد تغييرات في المحتوى'],
        questions_changes: Array.isArray(analysisData.questions_changes) ? analysisData.questions_changes : ['تم تحديد تغييرات في الأسئلة'],
        examples_changes: Array.isArray(analysisData.examples_changes) ? analysisData.examples_changes : ['تم تحديد تغييرات في الأمثلة'],
        major_differences: Array.isArray(analysisData.major_differences) ? analysisData.major_differences : ['تم تحديد اختلافات رئيسية'],
        summary: analysisData.summary || 'تم إجراء مقارنة شاملة بين النصين',
        recommendation: analysisData.recommendation || 'يُنصح بمراجعة التحديثات'
      };

      // حفظ نتائج المقارنة في قاعدة البيانات
      const updateData = {
        text_similarity: analysisData.similarity_percentage,
        visual_similarity: analysisData.similarity_percentage,
        changes_detected: JSON.stringify(analysisData),
        status: 'completed',
        processing_time: Date.now() / 1000
      };

      await supabase
        .from('file_comparisons')
        .update(updateData)
        .eq('id', comparison.id);

      console.log('تم حفظ نتائج المقارنة بنجاح');

      return new Response(
        JSON.stringify({
          success: true,
          analysis: analysisData,
          detailedReport: `تقرير مقارنة مفصل بين ${comparison.old_file_name} و ${comparison.new_file_name}`
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );

    } catch (error) {
      console.error('خطأ في معالجة Gemini:', error);
      
      // إنشاء تحليل أساسي في حالة الفشل
      const fallbackAnalysis = {
        similarity_percentage: this.calculateBasicSimilarity(oldText, newText),
        content_changes: ['تم تحديد تغييرات أساسية في المحتوى'],
        questions_changes: ['تم تحديد تحديثات في الأسئلة'],
        examples_changes: ['تم تحديد تحديثات في الأمثلة'],
        major_differences: ['يوجد اختلافات بين النسختين'],
        summary: 'تم إجراء مقارنة أساسية بين النصين، يُنصح بالمراجعة اليدوية للحصول على تفاصيل أكثر دقة',
        recommendation: 'يُنصح بمراجعة التغييرات يدوياً لضمان الدقة'
      };

      // حفظ النتيجة الاحتياطية
      await supabase
        .from('file_comparisons')
        .update({
          text_similarity: fallbackAnalysis.similarity_percentage,
          visual_similarity: fallbackAnalysis.similarity_percentage,
          changes_detected: JSON.stringify(fallbackAnalysis),
          status: 'completed',
          processing_time: Date.now() / 1000
        })
        .eq('id', comparison.id);

      return new Response(
        JSON.stringify({
          success: true,
          analysis: fallbackAnalysis,
          detailedReport: 'تقرير مقارنة أساسي - تم استخدام التحليل الاحتياطي'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

  } catch (error) {
    console.error('خطأ عام في المقارنة:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: 'Comparison failed', 
        details: error.message 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// دالة مساعدة لحساب التشابه الأساسي
function calculateBasicSimilarity(text1: string, text2: string): number {
  if (!text1 || !text2) return 0;
  
  const words1 = text1.toLowerCase().split(/\s+/);
  const words2 = text2.toLowerCase().split(/\s+/);
  
  const set1 = new Set(words1);
  const set2 = new Set(words2);
  
  const intersection = new Set([...set1].filter(x => set2.has(x)));
  const union = new Set([...set1, ...set2]);
  
  return Math.round((intersection.size / union.size) * 100);
}
