import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase';
import { getAnalyses, getAnalysisById } from '@/lib/db';

export const runtime = 'edge';

/**
 * GET /api/analyses
 * Fetch user's analysis history
 */
export async function GET(request: NextRequest) {
  try {
    // Require authentication
    const user = await requireAuth();

    // Get analysis ID from query params (if fetching single analysis)
    const { searchParams } = new URL(request.url);
    const analysisId = searchParams.get('id');

    if (analysisId) {
      // Fetch single analysis
      const analysis = await getAnalysisById(analysisId);

      if (!analysis) {
        return NextResponse.json(
          { error: 'Analysis not found' },
          { status: 404 }
        );
      }

      return NextResponse.json({
        success: true,
        analysis,
      });
    }

    // Fetch all user's analyses
    const analyses = await getAnalyses(user.id);

    return NextResponse.json({
      success: true,
      analyses,
      count: analyses.length,
    });

  } catch (error) {
    console.error('Error fetching analyses:', error);

    // Check if it's an authentication error
    if (error instanceof Error && error.message === 'Authentication required') {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Failed to fetch analyses',
      },
      { status: 500 }
    );
  }
}
