import { Download, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { FieldError, Hint, Input, Label, Select } from "@/components/ui/form";
import { ConfirmDialog, Skeleton } from "@/components/ui/misc";
import { useAsync } from "@/hooks/useAsync";
import { downloadJson, errorMessage, userApi } from "@/services/api";
import { useAuth } from "@/store/auth";
import type { Mode } from "@/types/api";
import { MODE_LABEL } from "@/utils/format";

export default function SettingsPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const privacy = useAsync(() => userApi.privacy());
  const [name, setName] = useState(user?.full_name ?? "");
  const [mode, setMode] = useState<Mode>(user?.preferences.default_mode ?? "semantic");
  const [countVerify, setCountVerify] = useState(!!user?.preferences.count_strong_semantic);
  const [equal, setEqual] = useState(!!user?.preferences.equal_weights);
  const [retention, setRetention] = useState<number>(user?.preferences.retention_days ?? 180);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [password, setPassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const nameError = name.trim().length < 2 ? "Enter at least 2 characters." : undefined;
  const retentionError = !Number.isInteger(retention) || retention < 1 || retention > 3650 ? "Choose between 1 and 3650 days." : undefined;

  const save = async () => {
    if (nameError || retentionError) return;
    setSaving(true);
    try {
      const updated = await userApi.update({ full_name: name.trim(), preferences: { default_mode: mode, count_strong_semantic: countVerify, equal_weights: equal, retention_days: retention } });
      setUser(updated);
      void privacy.reload();
      toast.success("Settings saved");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const exportAll = async () => {
    setExporting(true);
    try {
      downloadJson(await userApi.exportAll(), "skillgap-my-data.json");
      toast.success("Export downloaded");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setExporting(false);
    }
  };

  const deleteAccount = async () => {
    setDeleteError(null);
    try {
      await userApi.deleteAccount(password);
      setUser(null);
      toast.success("Account and all data deleted");
      navigate("/");
    } catch (e) {
      setDeleteError(errorMessage(e));
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader title="Profile" />
        <CardBody className="grid gap-4 sm:grid-cols-2">
          <div><Label htmlFor="name">Name</Label><Input id="name" value={name} aria-invalid={!!nameError} onChange={(e) => setName(e.target.value)} /><FieldError message={nameError} /></div>
          <div><Label htmlFor="email">Email</Label><Input id="email" value={user?.email ?? ""} disabled /><Hint>Email cannot be changed.</Hint></div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Analysis defaults" description="Used to pre-fill the new analysis form." />
        <CardBody className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="mode">Default matching method</Label>
            <Select id="mode" value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
              {(Object.keys(MODE_LABEL) as Mode[]).map((m) => <option key={m} value={m}>{MODE_LABEL[m]}</option>)}
            </Select>
            <Hint>The sentence-transformer model (all-MiniLM-L6-v2) is configured on the server with SEMANTIC_MODEL.</Hint>
          </div>
          <div className="space-y-3 pt-1 text-sm">
            <label className="flex items-start gap-2"><input type="checkbox" className="mt-0.5 h-4 w-4 accent-[var(--color-pine)]" checked={countVerify} onChange={(e) => setCountVerify(e.target.checked)} />Count “verify” matches toward coverage</label>
            <label className="flex items-start gap-2"><input type="checkbox" className="mt-0.5 h-4 w-4 accent-[var(--color-pine)]" checked={equal} onChange={(e) => setEqual(e.target.checked)} />Weight all requirements equally</label>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Privacy and data" />
        <CardBody className="space-y-5">
          {privacy.loading ? <Skeleton className="h-16" /> : privacy.data && <p className="text-sm text-muted">{privacy.data.statement}</p>}
          <div className="max-w-xs">
            <Label htmlFor="retention">Keep analyses for (days)</Label>
            <Input id="retention" type="number" min={1} max={3650} value={retention} aria-invalid={!!retentionError} onChange={(e) => setRetention(Number(e.target.value))} />
            <FieldError message={retentionError} />
            <Hint>Older analyses are deleted automatically when the server starts.</Hint>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" loading={exporting} onClick={exportAll}><Download className="h-4 w-4" aria-hidden /> Export all my data</Button>
          </div>
        </CardBody>
      </Card>

      <div className="flex justify-end"><Button loading={saving} disabled={!!nameError || !!retentionError} onClick={save}>Save settings</Button></div>

      <Card className="border-missing/30">
        <CardHeader title="Delete account" description="Permanently removes your account, resumes, job descriptions, analyses, roadmaps and corrections." />
        <CardBody><Button variant="danger" onClick={() => setConfirm(true)}><Trash2 className="h-4 w-4" aria-hidden /> Delete my account</Button></CardBody>
      </Card>

      <ConfirmDialog open={confirm} title="Delete your account?" body="This cannot be undone. Enter your password to confirm."
        confirmLabel="Delete everything" onConfirm={deleteAccount} onCancel={() => { setConfirm(false); setPassword(""); setDeleteError(null); }}>
        <div className="mt-4">
          <Label htmlFor="del-pw">Password</Label>
          <Input id="del-pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          <FieldError message={deleteError ?? undefined} />
        </div>
      </ConfirmDialog>
    </div>
  );
}
