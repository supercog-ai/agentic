'use client'
import Image from 'next/image';
import { signIn } from 'next-auth/react';

import { Button } from '@/components/ui/button';

// Loads when user redirected to /login
export default function LoginPage() {
  return (
    <div className="h-screen flex flex-col items-center justify-center">
      <h1 className="text-2xl font-bold mb-6">Sign in to Agentic</h1>
      <Button className="" onClick={() => signIn('google', { callbackUrl: '/' })}>
      <Image
        src="/google-icon.svg"
        width={20}
        height={20}
        alt="Google icon"
      />
      Sign in with Google
      </Button>
      <Button className="mt-5" onClick={() => signIn('github', { callbackUrl: '/' })}>
      <Image
        src="/github-icon.svg"
        width={20}
        height={20}
        alt="GitHub icon"
      />
      Sign in with GitHub
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
