import './globals.css'

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import React from 'react';

import { SWRProvider } from './providers/SWRProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Agentic Chat Interface',
  description: 'Interface for interacting with Agentic agents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SWRProvider>
          {children}
        </SWRProvider>
      </body>
    </html>
  )
}
