import { NextRequest, NextResponse } from 'next/server';
import { analyzeFlippaListing } from '@/lib/analyzer';

export const runtime = 'edge';
export const maxDuration = 60; // 60 seconds for analysis

interface AnalyzeRequest {
  url: string;
  listingData?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: AnalyzeRequest = await request.json();

    if (!body.url) {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      );
    }

    // Validate Flippa URL
    const flippaRegex = /^https?:\/\/(www\.)?flippa\.com\/.+/i;
    if (!flippaRegex.test(body.url)) {
      return NextResponse.json(
        { error: 'Please provide a valid Flippa listing URL' },
        { status: 400 }
      );
    }

    // For MVP, we'll ask users to paste the listing details
    // In Phase 2, we'll automatically scrape the page
    if (!body.listingData || body.listingData.trim().length < 100) {
      return NextResponse.json(
        {
          error: 'Please provide listing details (revenue, traffic, description, etc.).\n\nTip: Copy the key details from the Flippa page including price, revenue, profit, traffic stats, and description.'
        },
        { status: 400 }
      );
    }

    // Analyze the listing
    const analysis = await analyzeFlippaListing(body.listingData, body.url);

    return NextResponse.json({
      success: true,
      analysis,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Analysis error:', error);

    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Analysis failed',
        details: process.env.NODE_ENV === 'development' ? error : undefined,
      },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'FlipFlow Analyzer API',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
}
