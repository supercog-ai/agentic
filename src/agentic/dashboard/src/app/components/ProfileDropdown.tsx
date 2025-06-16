import { User } from 'lucide-react'
import { signOut, useSession } from 'next-auth/react';

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

export default function ProfileDropdown() {
    const { data: session } = useSession();
  
    const userName = session?.user?.name ?? 'Guest';
    
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className='rounded-full border bg-white shadow p-2 flex items-center'>
            <User className='h-5 w-6 ' />
            {/* <span className='font-medium'>{userName}</span> */}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align='end' className='min-w-[180px]'>
          <DropdownMenuLabel>
            <div className='font-semibold'>{userName}</div>
            <div className='text-xs text-muted-foreground'>{session?.user?.email}</div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => {
              if (!session) { // guest
                localStorage.removeItem('agentic-guest');
                window.location.href = '/login';
              } else {
                signOut({ callbackUrl: '/login' });
              }
            }}
            className='cursor-pointer text-red-600'
          >
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }
  