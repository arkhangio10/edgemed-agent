import { create } from "zustand";
import { signInAnonymously, signOut, onAuthStateChanged, User } from "firebase/auth";
import { auth } from "./firebase";

interface GuestAuthState {
  isAuthenticated: boolean;
  user: User | null;
  uid: string | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useGuestAuth = create<GuestAuthState>((set, get) => ({
  isAuthenticated: false,
  user: null,
  uid: null,
  loading: true,

  login: async () => {
    try {
      const cred = await signInAnonymously(auth);
      set({
        isAuthenticated: true,
        user: cred.user,
        uid: cred.user.uid,
        loading: false,
      });
    } catch (err) {
      console.error("Anonymous sign-in failed, using fallback session:", err);
      const fallbackId = `guest-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      sessionStorage.setItem("edgemed_guest", fallbackId);
      set({
        isAuthenticated: true,
        user: null,
        uid: fallbackId,
        loading: false,
      });
    }
  },

  logout: async () => {
    try {
      await signOut(auth);
    } catch {
      // ignore
    }
    sessionStorage.removeItem("edgemed_guest");
    set({ isAuthenticated: false, user: null, uid: null, loading: false });
  },
}));

onAuthStateChanged(auth, (user) => {
  if (user) {
    useGuestAuth.setState({
      isAuthenticated: true,
      user,
      uid: user.uid,
      loading: false,
    });
  } else {
    const fallback = sessionStorage.getItem("edgemed_guest");
    useGuestAuth.setState({
      isAuthenticated: !!fallback,
      user: null,
      uid: fallback,
      loading: false,
    });
  }
});
