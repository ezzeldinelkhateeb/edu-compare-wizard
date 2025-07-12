import { useState, useCallback, useRef } from 'react';
import React from 'react';
import { multilingualServices } from '../services/multilingualServices';

export interface BatchFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  result?: unknown;
  error?: string;
}

export interface BatchProcessingOptions {
  languagePreference?: string;
  enableLandingAI?: boolean;
  enableGemini?: boolean;
  maxConcurrent?: number;
  outputFormat?: 'json' | 'markdown' | 'both';
}

export interface BatchProcessingState {
  files: BatchFile[];
  isUploading: boolean;
  isProcessing: boolean;
  batchId?: string;
  uploadProgress: number;
  processingProgress: number;
  currentPhase: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  summary?: unknown;
  error?: string;
}

export function useBatchProcessing() {
  const [state, setState] = useState<BatchProcessingState>({
    files: [],
    isUploading: false,
    isProcessing: false,
    uploadProgress: 0,
    processingProgress: 0,
    currentPhase: 'idle',
  });

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Add files to the batch
  const addFiles = useCallback((newFiles: File[]) => {
    const batchFiles: BatchFile[] = newFiles.map((file, index) => ({
      file,
      id: `${Date.now()}-${index}`,
      status: 'pending',
      progress: 0,
    }));

    setState(prev => ({
      ...prev,
      files: [...prev.files, ...batchFiles],
      error: undefined,
    }));

    return batchFiles.map(f => f.id);
  }, []);

  // Remove a file from the batch
  const removeFile = useCallback((fileId: string) => {
    setState(prev => ({
      ...prev,
      files: prev.files.filter(f => f.id !== fileId),
    }));
  }, []);

  // Clear all files
  const clearFiles = useCallback(() => {
    setState(prev => ({
      ...prev,
      files: [],
      batchId: undefined,
      summary: undefined,
      error: undefined,
      currentPhase: 'idle',
    }));
  }, []);

  // Update file status
  const updateFileStatus = useCallback((fileId: string, updates: Partial<BatchFile>) => {
    setState(prev => ({
      ...prev,
      files: prev.files.map(f => 
        f.id === fileId ? { ...f, ...updates } : f
      ),
    }));
  }, []);

  // Simulate file upload
  const uploadFiles = useCallback(async (): Promise<{ batch_id: string } | null> => {
    if (state.files.length === 0) return null;

    setState(prev => ({
      ...prev,
      isUploading: true,
      currentPhase: 'uploading',
      uploadProgress: 0,
      error: undefined,
    }));

    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        setState(prev => ({ ...prev, uploadProgress: i }));
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const batchId = `batch_${Date.now()}`;
      
      setState(prev => ({
        ...prev,
        isUploading: false,
        batchId,
        uploadProgress: 100,
      }));

      // Mark all files as uploaded
      state.files.forEach(file => {
        updateFileStatus(file.id, { status: 'pending', progress: 100 });
      });

      return { batch_id: batchId };
    } catch (error) {
      setState(prev => ({
        ...prev,
        isUploading: false,
        currentPhase: 'failed',
        error: error instanceof Error ? error.message : 'فشل في رفع الملفات',
      }));

      return null;
    }
  }, [state.files, updateFileStatus]);

  // Start batch processing simulation
  const startProcessing = useCallback(async (options: BatchProcessingOptions = {}): Promise<boolean> => {
    if (!state.batchId) {
      setState(prev => ({ ...prev, error: 'لا يوجد دفعة للمعالجة' }));
      return false;
    }

    setState(prev => ({
      ...prev,
      isProcessing: true,
      currentPhase: 'processing',
      processingProgress: 0,
      error: undefined,
    }));

    try {
      // Simulate processing with progress updates
      for (let i = 0; i <= 100; i += 5) {
        setState(prev => ({ ...prev, processingProgress: i }));
        
        // Update file statuses based on progress
        const completedCount = Math.floor((i / 100) * state.files.length);
        state.files.forEach((file, index) => {
          if (index < completedCount) {
            updateFileStatus(file.id, { status: 'completed', progress: 100 });
          } else if (index === completedCount) {
            updateFileStatus(file.id, { status: 'processing', progress: 50 });
          }
        });

        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Mark all files as completed
      state.files.forEach(file => {
        updateFileStatus(file.id, { status: 'completed', progress: 100 });
      });

      setState(prev => ({
        ...prev,
        isProcessing: false,
        currentPhase: 'completed',
        processingProgress: 100,
        summary: {
          batch_summary: {
            total_files: state.files.length,
            successful_files: state.files.length,
            failed_files: 0,
            success_rate: 100
          },
          language_distribution: {
            ar: Math.floor(state.files.length / 2),
            en: Math.ceil(state.files.length / 2)
          }
        }
      }));

      return true;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isProcessing: false,
        currentPhase: 'failed',
        error: error instanceof Error ? error.message : 'فشل في المعالجة',
      }));
      return false;
    }
  }, [state.batchId, state.files, updateFileStatus]);

  // Get batch results (simulation)
  const getResults = useCallback(async () => {
    if (!state.batchId) return null;

    return {
      batch_id: state.batchId,
      summary: state.summary,
      individual_results: state.files.map(file => ({
        filename: file.file.name,
        status: file.status,
        result: file.result
      }))
    };
  }, [state.batchId, state.summary, state.files]);

  // Process files end-to-end
  const processFiles = useCallback(async (options: BatchProcessingOptions = {}): Promise<boolean> => {
    try {
      // Step 1: Upload files
      const uploadResult = await uploadFiles();
      if (!uploadResult) return false;

      // Step 2: Start processing
      const processingResult = await startProcessing(options);
      return processingResult;
    } catch (error) {
      console.error('Process files error:', error);
      return false;
    }
  }, [uploadFiles, startProcessing]);

  // Cleanup batch
  const cleanup = useCallback(async () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    setState({
      files: [],
      isUploading: false,
      isProcessing: false,
      uploadProgress: 0,
      processingProgress: 0,
      currentPhase: 'idle',
    });
  }, []);

  // Validate files before processing
  const validateFiles = useCallback((files: File[]): { valid: File[]; invalid: File[] } => {
    const validExtensions = ['.jpg', '.jpeg', '.png', '.pdf', '.md', '.txt', '.docx'];
    const valid: File[] = [];
    const invalid: File[] = [];

    files.forEach(file => {
      const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (validExtensions.includes(extension)) {
        valid.push(file);
      } else {
        invalid.push(file);
      }
    });

    return { valid, invalid };
  }, []);

  // Get summary statistics
  const getStatistics = useCallback(() => {
    const total = state.files.length;
    const completed = state.files.filter(f => f.status === 'completed').length;
    const failed = state.files.filter(f => f.status === 'failed').length;
    const processing = state.files.filter(f => f.status === 'processing').length;
    const pending = state.files.filter(f => f.status === 'pending').length;

    return {
      total,
      completed,
      failed,
      processing,
      pending,
      completionRate: total > 0 ? (completed / total) * 100 : 0,
      failureRate: total > 0 ? (failed / total) * 100 : 0,
    };
  }, [state.files]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  return {
    // State
    ...state,
    statistics: getStatistics(),
    
    // Actions
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles,
    startProcessing,
    processFiles,
    getResults,
    cleanup,
    
    // Utilities
    validateFiles,
  };
} 