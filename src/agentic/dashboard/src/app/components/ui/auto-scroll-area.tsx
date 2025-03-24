'use client'

import * as ScrollAreaPrimitive from '@radix-ui/react-scroll-area'
import * as React from 'react'

import { cn } from '@/lib/utils'
import { ScrollBar } from './scroll-area'

interface AutoScrollAreaProps extends React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root> {
  /**
   * Used to trigger auto-scrolling. When this value changes, the area will scroll to
   * the bottom if the user hasn't manually scrolled up.
   */
  scrollTrigger?: any;
  /**
   * Optional callback when auto-scroll state changes (scrolling mode or manual mode)
   */
  onAutoScrollChange?: (isAutoScrolling: boolean) => void;
}

const AutoScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  AutoScrollAreaProps
>(({ className, children, scrollTrigger, onAutoScrollChange, ...props }, ref) => {
  const viewportRef = React.useRef<HTMLDivElement>(null)
  const [userHasScrolled, setUserHasScrolled] = React.useState(false)
  const [prevScrollHeight, setPrevScrollHeight] = React.useState(0)
  
  // Scroll to bottom function
  const scrollToBottom = React.useCallback(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight
    }
  }, [])

  // Handle scroll event to detect manual user scrolling
  const handleScroll = React.useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const viewport = event.currentTarget
    const isAtBottom = viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 30
    
    // If user scrolls up, mark as manually scrolled
    if (!isAtBottom && !userHasScrolled) {
      setUserHasScrolled(true)
      onAutoScrollChange?.(false)
    }
    
    // If user scrolls back to bottom, reset to auto-scroll mode
    if (isAtBottom && userHasScrolled) {
      setUserHasScrolled(false)
      onAutoScrollChange?.(true)
    }
  }, [userHasScrolled, onAutoScrollChange])

  // Effect to track content changes and auto-scroll
  React.useEffect(() => {
    if (!viewportRef.current) return
    
    const viewport = viewportRef.current
    const currentScrollHeight = viewport.scrollHeight
    
    // If content has changed (scrollHeight increased)
    if (currentScrollHeight > prevScrollHeight) {
      // Scroll to bottom only if user hasn't manually scrolled up
      if (!userHasScrolled) {
        scrollToBottom()
      }
      
      setPrevScrollHeight(currentScrollHeight)
    }
  }, [scrollTrigger, prevScrollHeight, userHasScrolled, scrollToBottom])

  // Initial scroll to bottom
  React.useEffect(() => {
    scrollToBottom()
    // Wait a bit and scroll again to handle any delayed rendering
    const timeoutId = setTimeout(scrollToBottom, 100)
    return () => clearTimeout(timeoutId)
  }, [scrollToBottom])

  return (
    <ScrollAreaPrimitive.Root
      ref={ref}
      className={cn('relative overflow-hidden', className)}
      {...props}
    >
      <ScrollAreaPrimitive.Viewport 
        ref={viewportRef}
        className="h-full w-full rounded-[inherit]"
        onScroll={handleScroll}
      >
        {children}
      </ScrollAreaPrimitive.Viewport>
      <ScrollBar />
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  )
})
AutoScrollArea.displayName = 'AutoScrollArea'

export { AutoScrollArea }