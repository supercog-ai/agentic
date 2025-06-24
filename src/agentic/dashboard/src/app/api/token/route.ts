// app/api/token/route.ts
import { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function GET(req: NextRequest) {
    const token = await getToken({ req, secret: process.env.AUTH_SECRET , raw: true});
    return new Response(
      JSON.stringify({ token }), 
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
}
