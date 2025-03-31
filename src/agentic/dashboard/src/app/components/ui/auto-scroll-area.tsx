'use client'

import * as ScrollAreaPrimitive from '@radix-ui/react-scroll-area'
import { ArrowDown } from 'lucide-react'
import * as React from 'react'

import { cn } from '@/lib/utils'

import { ScrollBar } from './scroll-area'

interface AutoScrollAreaProps extends React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root> {
  /**
   * Used to trigger auto-scrolling. When this value changes, the area will scroll to
   * the bottom if the user hasn't manually scrolled up.
   */
  scrollTrigger?: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  /**
   * Optional callback when auto-scroll state changes (scrolling mode or manual mode)
   */
  onAutoScrollChange?: (_isAutoScrolling: boolean) => void;
  /**
   * Threshold in pixels to determine if user is at the bottom
   * Default: 30 pixels from bottom
   */
  bottomThreshold?: number;
  /**
   * Show the scroll-to-bottom button when auto-scroll is disabled
   * Default: true
   */
  showScrollButton?: boolean;
}

const AutoScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  AutoScrollAreaProps
>(({ 
  className, 
  children, 
  scrollTrigger, 
  onAutoScrollChange, 
  bottomThreshold = 30,
  showScrollButton = true,
  ...props 
}, ref) => {
  const viewportRef = React.useRef<HTMLDivElement>(null)
  const [userHasScrolled, setUserHasScrolled] = React.useState(false)
  const [prevScrollHeight, setPrevScrollHeight] = React.useState(0)
  const [isAtBottom, setIsAtBottom] = React.useState(true)
  
  // Scroll to bottom function
  const scrollToBottom = React.useCallback(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight
      // After scrolling to bottom, reset user scroll state
      setUserHasScrolled(false)
      onAutoScrollChange?.(true)
      setIsAtBottom(true)
    }
  }, [onAutoScrollChange])

  // Function to check if viewport is at bottom
  const checkIfAtBottom = React.useCallback((viewport: HTMLDivElement) => {
    return viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < bottomThreshold
  }, [bottomThreshold])

  // Handle scroll event to detect manual user scrolling
  const handleScroll = React.useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const viewport = event.currentTarget
    const atBottom = checkIfAtBottom(viewport)
    setIsAtBottom(atBottom)
    
    // If user scrolls up, mark as manually scrolled
    if (!atBottom && !userHasScrolled) {
      setUserHasScrolled(true)
      onAutoScrollChange?.(false)
    }
    
    // If user scrolls back to bottom, reset to auto-scroll mode
    if (atBottom && userHasScrolled) {
      setUserHasScrolled(false)
      onAutoScrollChange?.(true)
    }
  }, [userHasScrolled, onAutoScrollChange, checkIfAtBottom])

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
    <div className="relative">
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
      
      {showScrollButton && userHasScrolled && !isAtBottom && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground shadow-md hover:bg-primary/90 transition-opacity"
          title="Scroll to bottom (enables auto-scroll)"
          type="button"
        >
          <ArrowDown size={16} />
        </button>
      )}
    </div>
  )
})
AutoScrollArea.displayName = 'AutoScrollArea'

export { AutoScrollArea }
