import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const url = searchParams.get('url');

    if (!url) {
        console.error('[Image Proxy] Missing URL parameter');
        return new NextResponse('Missing URL parameter', { status: 400 });
    }

    // Check for invalid URLs
    if (url === 'undefined' || url === 'null' || !url.startsWith('http')) {
        console.error('[Image Proxy] Invalid URL:', url);
        return new NextResponse(`Invalid URL: ${url}`, { status: 400 });
    }

    try {
        const urlObj = new URL(url);
        const isNongsaro = urlObj.hostname.includes('nongsaro.go.kr');
        const isThesool = urlObj.hostname.includes('thesool.com');

        // Build referer based on site
        let referer = urlObj.origin + '/';
        if (isNongsaro) referer = 'https://www.nongsaro.go.kr/';
        if (isThesool) referer = 'https://thesool.com/';

        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': referer,
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
        });

        if (!response.ok) {
            console.error(`[Image Proxy] Fetch failed: ${url} - Status: ${response.status} ${response.statusText}`);
            return new NextResponse(`Failed to fetch image: ${response.statusText}`, { status: response.status });
        }

        const contentType = response.headers.get('content-type') || 'application/octet-stream';

        // 🖼️ Resize & Optimize with Sharp (Solves 413 Payload Too Large)
        // If content-type is image, resize it. Otherwise stream as is.
        if (contentType.startsWith('image/')) {
            try {
                const sharp = require('sharp');
                const transformer = sharp()
                    .resize({ width: 800, withoutEnlargement: true }) // Reasonable max width
                    .webp({ quality: 80 }); // Compress to WebP

                // Pipe: Fetch Body -> Sharp -> Response
                // Note: NextResponse takes a ReadableStream. Sharp returns a Node Stream.
                // We need to convert or just return the Node Stream if compatible, 
                // but Next.js App Router prefers standard Web Streams.
                // However, passing a Node stream to NextResponse body often works in Node runtimes.
                // Safer: Buffer it if it's small enough after resize?
                // Or use iterator.

                // Let's try buffering the *resized* image. Resized WebP (800w) is usually < 100KB.
                // This is safe for Lambda memory (unlike the 10MB raw original).
                const buffer = await response.arrayBuffer();
                const resizedBuffer = await sharp(Buffer.from(buffer))
                    .resize({ width: 800, withoutEnlargement: true })
                    .webp({ quality: 80 })
                    .toBuffer();

                return new NextResponse(resizedBuffer, {
                    headers: {
                        'Content-Type': 'image/webp',
                        'Cache-Control': 'public, max-age=31536000, immutable',
                        'X-Image-Tansformed': 'true'
                    }
                });
            } catch (sharpError) {
                console.error('[Image Proxy] Sharp processing failed:', sharpError);
                // Fallback to original stream if sharp fails (or not installed)
                return new NextResponse(response.body, {
                    headers: {
                        'Content-Type': contentType,
                        'Cache-Control': 'public, max-age=31536000, immutable'
                    }
                });
            }
        }

        // Non-image or Sharp missing --> Stream original
        return new NextResponse(response.body, {
            headers: {
                'Content-Type': contentType,
                'Cache-Control': 'public, max-age=31536000, immutable'
            }
        });
    } catch (error) {
        console.error('[Image Proxy] Error fetching:', url, error);

        // Return a placeholder image instead of error
        // 1x1 transparent PNG as fallback
        const placeholderPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
        return new NextResponse(placeholderPng, {
            headers: {
                'Content-Type': 'image/png',
                'Cache-Control': 'public, max-age=3600'
            }
        });
    }
}
