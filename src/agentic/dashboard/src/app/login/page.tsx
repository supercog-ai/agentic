'use client'
import { signIn } from "next-auth/react";
import { Button } from '@/components/ui/button';

// Loads when user redirected to /login
export default function LoginPage() {
  return (
    <div className="h-screen flex flex-col items-center justify-center">
      <h1 className="text-2xl font-bold mb-6">Sign in to Agentic</h1>
      <Button onClick={() => signIn('google', { callbackUrl: '/' })}>
      <img
        src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
        alt="Google logo"
        className="h-5 w-5 mr-2 inline-block"
        style={{ verticalAlign: 'middle' }}
      />
        Sign in with Google
      </Button>
      <Button
        variant="ghost"
        className="mt-4"
        onClick={() => {
          localStorage.setItem('agentic-guest', '1');
          window.location.href = '/';
        }}
      >
        Continue as Guest
      </Button>
    </div>
  )
}
