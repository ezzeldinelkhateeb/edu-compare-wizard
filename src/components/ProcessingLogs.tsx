import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Terminal, ChevronDown, ChevronUp } from 'lucide-react';

export interface LogEntry {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'processing';
}

interface ProcessingLogsProps {
  logs: LogEntry[];
  title?: string;
  maxHeight?: string;
  className?: string;
  autoScroll?: boolean;
}

const ProcessingLogs: React.FC<ProcessingLogsProps> = ({
  logs,
  title = 'سجل العمليات الخلفية',
  maxHeight = '300px',
  className = '',
  autoScroll = true
}) => {
  const [showLogs, setShowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll logs to bottom when new logs arrive
  useEffect(() => {
    if (logsEndRef.current && showLogs && autoScroll) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, showLogs, autoScroll]);

  // Format timestamp to local time
  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  return (
    <Card className={`border-2 border-gray-200 ${className}`}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Terminal className="w-5 h-5" />
            {title}
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setShowLogs(!showLogs)}
            className="text-gray-600"
          >
            {showLogs ? (
              <>
                <ChevronUp className="w-4 h-4 ml-1" />
                إخفاء
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 ml-1" />
                إظهار
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      {showLogs && (
        <CardContent className="p-0">
          <ScrollArea className={`border-t border-gray-200 bg-gray-50 rounded-b-lg font-mono text-sm`} style={{ maxHeight }}>
            <div className="p-4 space-y-1">
              {logs.length === 0 ? (
                <div className="text-gray-500 text-center py-4">
                  لا توجد سجلات حتى الآن...
                </div>
              ) : (
                logs.map((log, index) => (
                  <div 
                    key={index} 
                    className={`py-1 ${
                      log.type === 'error' ? 'text-red-600' : 
                      log.type === 'success' ? 'text-green-600' : 
                      log.type === 'warning' ? 'text-amber-600' : 
                      log.type === 'processing' ? 'text-blue-600' : 
                      'text-gray-700'
                    }`}
                  >
                    <span className="text-gray-500 ml-2">
                      [{formatTimestamp(log.timestamp)}]
                    </span>
                    <span>{log.message}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  );
};

export default ProcessingLogs; 