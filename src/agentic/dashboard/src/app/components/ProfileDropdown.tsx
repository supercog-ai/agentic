import { User } from 'lucide-react'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuLabel, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { signOut, useSession } from "next-auth/react";
import { getToken } from "next-auth/jwt";
import type { NextApiRequest, NextApiResponse } from "next";
import { useEffect } from "react";

export default function ProfileDropdown() {
    const { data: session } = useSession();
  
    const userName = session?.user?.name ?? "Guest";

    useEffect(() => {
      async function fetchToken() {
        const res = await fetch("/api/token", { credentials: "include" });
        const data = await res.json();
        // console.log("NextAuth JWT token:", data.token); 
        console.log("NextAuth JWT token:", data); 
      }
      fetchToken();
    }, []);
    
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="rounded-full border bg-white shadow p-2 flex items-center">
            <User className="h-5 w-6 " />
            {/* <span className="font-medium">{userName}</span> */}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-[180px]">
          <DropdownMenuLabel>
            <div className="font-semibold">{userName}</div>
            <div className="text-xs text-muted-foreground">{session?.user?.email}</div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => {
              if (!session) { // guest
                localStorage.removeItem('agentic-guest');
                window.location.href = "/login";
              } else {
                signOut({ callbackUrl: "/login" });
              }
            }}
            className="cursor-pointer text-red-600"
          >
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }
  