import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { usePatientStore } from "@/lib/patient-store";
import { MOCK_RECORDS_LIST } from "@/lib/mock-data";
import { Search } from "lucide-react";

export default function Records() {
  const [search, setSearch] = useState("");
  const { records: patientRecords, selectedPatientId } = usePatientStore();

  const realRecords = patientRecords
    .filter((r) => !selectedPatientId || r.patientId === selectedPatientId)
    .map((r) => ({
      note_id: r.id,
      created_at: r.createdAt,
      completeness: r.safetyFlags?.completeness_score
        ? typeof r.safetyFlags.completeness_score === "number" && r.safetyFlags.completeness_score <= 1
          ? Math.round(r.safetyFlags.completeness_score * 100)
          : Math.round(r.safetyFlags.completeness_score)
        : 0,
      flags_count: (r.safetyFlags?.missing_fields?.length || 0) + (r.safetyFlags?.contradictions?.length || 0),
      status: r.status,
    }));

  const allRecords = realRecords.length > 0
    ? realRecords
    : MOCK_RECORDS_LIST.map((r) => ({
        ...r,
        completeness: typeof r.completeness === "number" && r.completeness <= 1
          ? Math.round(r.completeness * 100)
          : r.completeness,
      }));

  const filtered = allRecords.filter((r) =>
    r.note_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Records</h2>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by note ID..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search records"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Note ID</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Completeness</TableHead>
                <TableHead>Flags</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No records found. Extract a clinical note first.
                  </TableCell>
                </TableRow>
              )}
              {filtered.map((r) => (
                <TableRow key={r.note_id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell>
                    <Link to={`/app/records/${r.note_id}`} className="font-medium text-primary hover:underline">
                      {r.note_id.length > 16 ? `${r.note_id.slice(0, 16)}...` : r.note_id}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(r.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <StatusBadge variant={r.completeness >= 85 ? "success" : r.completeness >= 70 ? "warning" : "error"}>
                      {r.completeness}%
                    </StatusBadge>
                  </TableCell>
                  <TableCell>
                    {r.flags_count > 0 ? (
                      <StatusBadge variant="warning">{r.flags_count} flags</StatusBadge>
                    ) : (
                      <StatusBadge variant="success">Clean</StatusBadge>
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge variant="neutral">{r.status}</StatusBadge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
