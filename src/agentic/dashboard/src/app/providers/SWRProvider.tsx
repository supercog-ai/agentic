// src/app/providers/SWRProvider.tsx
'use client';

import { ReactNode } from 'react';
import { SWRConfig } from 'swr';

interface SWRProviderProps {
  children: ReactNode;
}

export function SWRProvider({ children }: SWRProviderProps) {
  return (
    <SWRConfig
      value={{
        // Global SWR configurations
        revalidateOnFocus: true, // Auto revalidate when window gets focused
        revalidateOnReconnect: true, // Auto revalidate when browser regains connection
        errorRetryCount: 3, // Retry failed requests 3 times
        dedupingInterval: 2000, // Deduplicate requests with the same key in 2 seconds
        focusThrottleInterval: 5000, // Only revalidate at most once every 5 seconds on focus events
        loadingTimeout: 3000, // Timeout to trigger the onLoadingSlow event
        onError: (error, key) => {
          console.error(`SWR Error for ${key}:`, error);
        }
      }}
    >
      {children}
    </SWRConfig>
  );
}
