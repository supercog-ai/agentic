// app/api/[...path]/route.ts
import { NextRequest } from 'next/server';

// Helper function to safely clone request with duplex option
async function forwardRequest(request: NextRequest, targetUrl: string) {
  const headers = new Headers(request.headers);
  
  // Strip any host header as it will be set by fetch for the target
  headers.delete('host');
  
  const method = request.method;
  
  // For methods that might have a body
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    // Read body as text to avoid streaming issues
    let body = null;
    
    try {
      // Only try to read body if content-length exists and is not 0
      const contentLength = request.headers.get('content-length');
      if (contentLength && parseInt(contentLength) > 0) {
        body = await request.text();
      }
    } catch (e) {
      console.error('Error reading request body:', e);
    }
    
    return fetch(targetUrl, {
      method,
      headers,
      body,
    });
  } else {
    // For methods without a body
    return fetch(targetUrl, {
      method,
      headers,
    });
  }
}

// Handle GET requests
export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = new URL(request.url);
  const isSSE = path.includes('getevents') && url.searchParams.get('stream') === 'true';
  
  const backendUrl = `http://localhost:8086/${path}${url.search}`;
  
  // Special handling for SSE
  if (isSSE) {
    const { readable, writable } = new TransformStream();
    
    fetch(backendUrl, {
      method: 'GET',
      headers: new Headers(request.headers),
      signal: request.signal,
    }).then(backendResponse => {
      if (!backendResponse.ok) {
        const writer = writable.getWriter();
        writer.write(new TextEncoder().encode(`data: {'error':'Backend error ${backendResponse.status}'}\n\n`));
        writer.close();
        return;
      }
      
      if (backendResponse.body) {
        backendResponse.body.pipeTo(writable).catch(err => {
          // Check if this is an aborted response (client disconnected)
          if (err.name === 'AbortError' || err.message.includes('aborted') || 
              err.name === 'ResponseAborted') {
            // This is normal for SSE when client disconnects, so just log at debug level
            console.debug('Client disconnected from SSE stream');
          } else {
            // Log other errors as they might be important
            console.error('Error piping response:', err);
          }
        });
      } else {
        const writer = writable.getWriter();
        writer.write(new TextEncoder().encode('data: {\'error\':\'No response body\'}\n\n'));
        writer.close();
      }
    }).catch(error => {
      // Handle fetch errors
      console.error('Fetch error:', error);
      const writer = writable.getWriter();
      writer.write(new TextEncoder().encode('data: {\'error\':\'Fetch error\'}\n\n'));
      writer.close();
    });
    
    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      },
    });
  }
  
  // For regular GET requests
  const backendResponse = await fetch(backendUrl, {
    method: 'GET',
    headers: new Headers(request.headers),
  });
  
  const responseHeaders = new Headers(backendResponse.headers);
  
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

// Handle POST requests
export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = new URL(request.url);
  const backendUrl = `http://localhost:8086/${path}${url.search}`;
  
  const backendResponse = await forwardRequest(request, backendUrl);
  
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: new Headers(backendResponse.headers),
  });
}

// Handle DELETE requests
export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = new URL(request.url);
  const backendUrl = `http://localhost:8086/${path}${url.search}`;
  
  const backendResponse = await forwardRequest(request, backendUrl);
  
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: new Headers(backendResponse.headers),
  });
}

// Handle PUT requests
export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = new URL(request.url);
  const backendUrl = `http://localhost:8086/${path}${url.search}`;
  
  const backendResponse = await forwardRequest(request, backendUrl);
  
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: new Headers(backendResponse.headers),
  });
}

// Handle PATCH requests
export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = new URL(request.url);
  const backendUrl = `http://localhost:8086/${path}${url.search}`;
  
  const backendResponse = await forwardRequest(request, backendUrl);
  
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: new Headers(backendResponse.headers),
  });
}

export const dynamic = 'force-dynamic';
