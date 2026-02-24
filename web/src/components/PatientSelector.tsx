import { useState } from "react";
import { usePatientStore, Patient } from "@/lib/patient-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { UserPlus, Trash2, Users } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function PatientSelector() {
  const { patients, selectedPatientId, selectPatient, addPatient, deletePatient } = usePatientStore();
  const [newName, setNewName] = useState("");
  const [newAge, setNewAge] = useState("");
  const [newSex, setNewSex] = useState("Female");
  const [dialogOpen, setDialogOpen] = useState(false);
  const { toast } = useToast();

  const handleAdd = () => {
    if (!newName.trim() || !newAge.trim()) return;
    const id = addPatient({ name: newName.trim(), age: parseInt(newAge), sex: newSex });
    selectPatient(id);
    setNewName("");
    setNewAge("");
    setDialogOpen(false);
    toast({ title: "Patient added" });
  };

  const handleDelete = (id: string) => {
    deletePatient(id);
    toast({ title: "Patient deleted" });
  };

  const selected = patients.find((p) => p.id === selectedPatientId);

  return (
    <div className="flex items-center gap-2">
      <Users className="h-4 w-4 text-muted-foreground shrink-0" />
      <Select value={selectedPatientId || ""} onValueChange={(v) => selectPatient(v || null)}>
        <SelectTrigger className="w-48 h-8 text-xs" aria-label="Select patient">
          <SelectValue placeholder="Select patient..." />
        </SelectTrigger>
        <SelectContent>
          {patients.map((p) => (
            <SelectItem key={p.id} value={p.id} className="text-xs">
              {p.name} ({p.age}{p.sex[0]})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Add patient */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Add patient">
            <UserPlus className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Add New Patient</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input placeholder="Full name" value={newName} onChange={(e) => setNewName(e.target.value)} />
            <div className="flex gap-2">
              <Input placeholder="Age" type="number" className="w-20" value={newAge} onChange={(e) => setNewAge(e.target.value)} />
              <Select value={newSex} onValueChange={setNewSex}>
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Female">Female</SelectItem>
                  <SelectItem value="Male">Male</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" size="sm">Cancel</Button>
            </DialogClose>
            <Button size="sm" onClick={handleAdd} disabled={!newName.trim() || !newAge.trim()}>
              Add Patient
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete patient */}
      {selectedPatientId && (
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" aria-label="Delete patient">
              <Trash2 className="h-4 w-4" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete patient?</AlertDialogTitle>
              <AlertDialogDescription>
                This will delete {selected?.name} and all their records. This cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={() => handleDelete(selectedPatientId)}>Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
}
