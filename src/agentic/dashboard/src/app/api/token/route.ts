// app/api/token/route.ts
import { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export async function GET(req: NextRequest) {
    const decoded = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET , raw: true});
    return new Response(JSON.stringify({ token, decoded }), {
    headers: { "Content-Type": "application/json" },
  });
}
