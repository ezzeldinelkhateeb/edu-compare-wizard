
// خدمة تصدير التقارير
export interface ReportData {
  totalFiles: number;
  identicalFiles: number;
  changedFiles: number;
  averageSimilarity: number;
  processingTime: number;
  detailedResults: Array<{
    fileName: string;
    visualSimilarity: number;
    textSimilarity: number;
    overallScore: number;
    changes: string[];
    status: string;
  }>;
}

class ReportService {
  private static instance: ReportService;
  
  static getInstance(): ReportService {
    if (!ReportService.instance) {
      ReportService.instance = new ReportService();
    }
    return ReportService.instance;
  }

  // إنشاء تقرير PDF
  async generatePDFReport(data: ReportData): Promise<Blob> {
    // في التطبيق الحقيقي، سيتم استخدام مكتبة مثل jsPDF
    return new Promise((resolve) => {
      setTimeout(() => {
        const reportContent = this.generateReportHTML(data);
        const blob = new Blob([reportContent], { type: 'text/html' });
        resolve(blob);
      }, 2000);
    });
  }

  // إنشاء عرض PowerPoint
  async generatePowerPointReport(data: ReportData): Promise<Blob> {
    // في التطبيق الحقيقي، سيتم استخدام مكتبة مثل PptxGenJS
    return new Promise((resolve) => {
      setTimeout(() => {
        const pptContent = this.generatePowerPointContent(data);
        const blob = new Blob([pptContent], { 
          type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' 
        });
        resolve(blob);
      }, 3000);
    });
  }

  // تحميل الملف
  downloadFile(blob: Blob, fileName: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  private generateReportHTML(data: ReportData): string {
    return `
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>تقرير مقارنة المناهج التعليمية</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }
        .header { 
            text-align: center; 
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .summary { 
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .summary-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-number {
            font-size: 2rem;
            font-weight: bold;
            color: #3b82f6;
        }
        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .results-table th, .results-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
        }
        .results-table th {
            background: #3b82f6;
            color: white;
        }
        .status-identical { background: #dcfce7; }
        .status-minor { background: #fef3c7; }
        .status-major { background: #fed7aa; }
        .status-different { background: #fecaca; }
    </style>
</head>
<body>
    <div class="header">
        <h1>تقرير مقارنة المناهج التعليمية</h1>
        <p>تم إنشاؤه في: ${new Date().toLocaleDateString('ar-SA')}</p>
    </div>

    <div class="summary">
        <h2>الملخص التنفيذي</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-number">${data.totalFiles}</div>
                <div>إجمالي الملفات</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">${data.identicalFiles}</div>
                <div>ملفات متطابقة</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">${data.changedFiles}</div>
                <div>ملفات متغيرة</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">${Math.round(data.averageSimilarity)}%</div>
                <div>متوسط التطابق</div>
            </div>
        </div>
    </div>

    <h2>النتائج التفصيلية</h2>
    <table class="results-table">
        <thead>
            <tr>
                <th>اسم الملف</th>
                <th>التطابق البصري</th>
                <th>التطابق النصي</th>
                <th>النتيجة الإجمالية</th>
                <th>الحالة</th>
                <th>عدد التغييرات</th>
            </tr>
        </thead>
        <tbody>
            ${data.detailedResults.map(result => `
                <tr class="status-${result.status}">
                    <td>${result.fileName}</td>
                    <td>${result.visualSimilarity}%</td>
                    <td>${result.textSimilarity}%</td>
                    <td>${result.overallScore}%</td>
                    <td>${result.status}</td>
                    <td>${result.changes.length}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>تم إنشاء هذا التقرير بواسطة نظام مقارن المناهج التعليمية</p>
    </div>
</body>
</html>`;
  }

  private generatePowerPointContent(data: ReportData): string {
    // محاكاة محتوى PowerPoint (في التطبيق الحقيقي سيتم استخدام PptxGenJS)
    return `PowerPoint Content for ${data.totalFiles} files comparison`;
  }
}

export const reportService = ReportService.getInstance();
