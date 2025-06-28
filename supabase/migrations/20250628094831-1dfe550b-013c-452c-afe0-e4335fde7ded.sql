
-- إنشاء جدول لحفظ جلسات المقارنة
CREATE TABLE public.comparison_sessions (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users,
    session_name TEXT NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    processed_files INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- إنشاء جدول لحفظ نتائج المقارنة لكل ملف
CREATE TABLE public.file_comparisons (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES public.comparison_sessions(id) ON DELETE CASCADE,
    old_file_name TEXT NOT NULL,
    new_file_name TEXT NOT NULL,
    old_file_url TEXT,
    new_file_url TEXT,
    visual_similarity DECIMAL(5,2) NOT NULL DEFAULT 0,
    text_similarity DECIMAL(5,2) NOT NULL DEFAULT 0,
    extracted_text_old TEXT,
    extracted_text_new TEXT,
    changes_detected JSONB DEFAULT '[]',
    processing_time DECIMAL(8,3) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- إنشاء جدول لحفظ التقارير المُصدّرة
CREATE TABLE public.exported_reports (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES public.comparison_sessions(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('pdf', 'powerpoint', 'excel')),
    report_data JSONB NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- تفعيل Row Level Security
ALTER TABLE public.comparison_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exported_reports ENABLE ROW LEVEL SECURITY;

-- سياسات الأمان للجلسات
CREATE POLICY "Users can view their own sessions" 
    ON public.comparison_sessions 
    FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own sessions" 
    ON public.comparison_sessions 
    FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions" 
    ON public.comparison_sessions 
    FOR UPDATE 
    USING (auth.uid() = user_id);

-- سياسات الأمان لنتائج المقارنة
CREATE POLICY "Users can view comparisons from their sessions" 
    ON public.file_comparisons 
    FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.comparison_sessions 
        WHERE id = session_id AND user_id = auth.uid()
    ));

CREATE POLICY "Users can create comparisons for their sessions" 
    ON public.file_comparisons 
    FOR INSERT 
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.comparison_sessions 
        WHERE id = session_id AND user_id = auth.uid()
    ));

CREATE POLICY "Users can update comparisons from their sessions" 
    ON public.file_comparisons 
    FOR UPDATE 
    USING (EXISTS (
        SELECT 1 FROM public.comparison_sessions 
        WHERE id = session_id AND user_id = auth.uid()
    ));

-- سياسات الأمان للتقارير
CREATE POLICY "Users can view reports from their sessions" 
    ON public.exported_reports 
    FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.comparison_sessions 
        WHERE id = session_id AND user_id = auth.uid()
    ));

CREATE POLICY "Users can create reports for their sessions" 
    ON public.exported_reports 
    FOR INSERT 
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.comparison_sessions 
        WHERE id = session_id AND user_id = auth.uid()
    ));

-- إنشاء bucket لتخزين الملفات المرفوعة
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'comparison-files',
    'comparison-files',
    false,
    52428800, -- 50MB
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'application/pdf']::text[]
);

-- سياسات تخزين الملفات
CREATE POLICY "Users can upload their own files" 
    ON storage.objects 
    FOR INSERT 
    WITH CHECK (bucket_id = 'comparison-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own files" 
    ON storage.objects 
    FOR SELECT 
    USING (bucket_id = 'comparison-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own files" 
    ON storage.objects 
    FOR UPDATE 
    USING (bucket_id = 'comparison-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own files" 
    ON storage.objects 
    FOR DELETE 
    USING (bucket_id = 'comparison-files' AND auth.uid()::text = (storage.foldername(name))[1]);

-- إنشاء فهارس لتحسين الأداء
CREATE INDEX idx_comparison_sessions_user_id ON public.comparison_sessions(user_id);
CREATE INDEX idx_comparison_sessions_status ON public.comparison_sessions(status);
CREATE INDEX idx_file_comparisons_session_id ON public.file_comparisons(session_id);
CREATE INDEX idx_file_comparisons_status ON public.file_comparisons(status);
CREATE INDEX idx_exported_reports_session_id ON public.exported_reports(session_id);
