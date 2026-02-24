import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useGuestAuth } from "@/lib/guest-auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UserCircle, ArrowLeft, Loader2 } from "lucide-react";

export default function Auth() {
  const { isAuthenticated, loading, login } = useGuestAuth();
  const navigate = useNavigate();
  const [signingIn, setSigningIn] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated) navigate("/app/workspace", { replace: true });
  }, [isAuthenticated, loading, navigate]);

  const handleGuest = async () => {
    setSigningIn(true);
    await login();
    navigate("/app/workspace");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-hero">
            <span className="text-xl font-bold text-primary-foreground">E</span>
          </div>
          <CardTitle className="text-xl">Welcome to EdgeMed Agent</CardTitle>
          <CardDescription>
            No password needed. Start a temporary guest session to explore the demo.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            className="w-full gap-2 bg-gradient-hero hover:opacity-90 text-primary-foreground"
            size="lg"
            onClick={handleGuest}
            disabled={signingIn || loading}
          >
            {signingIn ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <UserCircle className="h-5 w-5" />
                Continue as Guest
              </>
            )}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            Temporary session for judges. No data is persisted beyond this session.
          </p>
          <div className="pt-2 text-center">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/" className="gap-1">
                <ArrowLeft className="h-3 w-3" />
                Back to home
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
