import { X, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface RiskReportPanelProps {
  onClose: () => void;
}

export const RiskReportPanel = ({ onClose }: RiskReportPanelProps) => {
  return (
    <div className="h-full bg-card rounded-xl shadow-soft border border-border overflow-hidden flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border bg-medical-pink/10">
        <h2 className="text-xl font-semibold text-foreground">Risk Assessment Report</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="text-foreground hover:bg-muted"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          {/* Risk Score */}
          <div className="bg-gradient-to-br from-medical-pink/10 to-medical-blue/10 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-medical-pink/20">
                <TrendingUp className="h-6 w-6 text-medical-pink" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">Overall Risk Score</h3>
                <p className="text-sm text-muted-foreground">Based on comprehensive analysis</p>
              </div>
            </div>
            <div className="text-4xl font-bold text-medical-pink">68%</div>
            <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full w-[68%] bg-gradient-to-r from-medical-pink to-medical-blue rounded-full" />
            </div>
          </div>

          {/* Risk Factors */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-foreground">Key Risk Factors</h3>
            
            <div className="flex items-start gap-3 p-4 bg-destructive/5 rounded-lg border border-destructive/20">
              <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="font-medium text-foreground">Gestational Hypertension</p>
                <p className="text-sm text-muted-foreground">Blood pressure readings consistently above normal range</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-destructive/5 rounded-lg border border-destructive/20">
              <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="font-medium text-foreground">Advanced Maternal Age</p>
                <p className="text-sm text-muted-foreground">Age-related pregnancy complications require monitoring</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-primary/5 rounded-lg border border-primary/20">
              <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium text-foreground">Regular Prenatal Care</p>
                <p className="text-sm text-muted-foreground">Consistent attendance at scheduled appointments</p>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-foreground">AI Recommendations</h3>
            
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium text-foreground mb-2">Immediate Actions</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-medical-blue">•</span>
                  <span>Schedule blood pressure monitoring every 48 hours</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-medical-blue">•</span>
                  <span>Order complete metabolic panel and urine analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-medical-blue">•</span>
                  <span>Consider consultation with maternal-fetal medicine specialist</span>
                </li>
              </ul>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium text-foreground mb-2">Long-term Management</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-medical-pink">•</span>
                  <span>Weekly non-stress tests starting at 32 weeks</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-medical-pink">•</span>
                  <span>Maintain strict diet and exercise regimen</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-medical-pink">•</span>
                  <span>Plan for potential early delivery at 37-38 weeks</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};
