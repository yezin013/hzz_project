import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // 캐싱 방지

export async function GET() {
    // 민감한 정보는 마스킹하거나 존재 여부만 리턴
    return NextResponse.json({
        system: {
            NODE_ENV: process.env.NODE_ENV,
            NEXTAUTH_URL: process.env.NEXTAUTH_URL,
            VERCEL_URL: process.env.VERCEL_URL,
        },
        cognito: {
            COGNITO_CLIENT_ID: process.env.COGNITO_CLIENT_ID,
            NEXT_PUBLIC_COGNITO_CLIENT_ID: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID,
            COGNITO_ISSUER: process.env.COGNITO_ISSUER,
            // NEXT_PUBLIC_COGNITO_DOMAIN: process.env.NEXT_PUBLIC_COGNITO_DOMAIN,
        },
        secrets: {
            HAS_NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET,
            HAS_AUTH_SECRET: !!process.env.AUTH_SECRET,
            SECRET_LEN: process.env.NEXTAUTH_SECRET?.length || 0,
        }
    });
}
