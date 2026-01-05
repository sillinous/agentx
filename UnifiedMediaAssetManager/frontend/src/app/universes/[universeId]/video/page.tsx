'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getUniverseById, Universe, VideoJob } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import VideoGenerator from '@/components/VideoGenerator';

export default function VideoGenerationPage() {
    const params = useParams();
    const { universeId } = params;

    const [universe, setUniverse] = useState<Universe | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [generatedVideos, setGeneratedVideos] = useState<VideoJob[]>([]);
    const isClient = useIsClient();

    useEffect(() => {
        if (isClient && typeof universeId === 'string') {
            loadUniverse();
        }
    }, [isClient, universeId]);

    const loadUniverse = async () => {
        try {
            setIsLoading(true);
            const data = await getUniverseById(universeId as string);
            if (data) {
                setUniverse(data);
            } else {
                setError('Universe not found');
            }
        } catch (err) {
            setError('Failed to load universe');
        } finally {
            setIsLoading(false);
        }
    };

    const handleVideoGenerated = (job: VideoJob) => {
        setGeneratedVideos((prev) => [job, ...prev]);
    };

    if (!isClient || isLoading) {
        return (
            <div className="px-4 py-6 sm:px-0">
                <p className="text-gray-600">Loading...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="px-4 py-6 sm:px-0">
                <h1 className="text-2xl font-bold text-red-600 mb-4">{error}</h1>
                <Link href="/" className="text-indigo-600 hover:underline">
                    &larr; Back to universes
                </Link>
            </div>
        );
    }

    return (
        <div className="px-4 py-6 sm:px-0">
            {/* Navigation */}
            <Link
                href={`/universes/${universeId}`}
                className="text-indigo-600 hover:underline mb-6 block"
            >
                &larr; Back to {universe?.name || 'Universe'}
            </Link>

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900">Video Generation</h1>
                <p className="text-lg text-gray-600 mt-2">
                    Create AI-generated videos for {universe?.name}
                </p>
            </div>

            {/* Video Generator Component */}
            <VideoGenerator
                universeId={universeId as string}
                onVideoGenerated={handleVideoGenerated}
            />

            {/* Generated Videos Gallery */}
            {generatedVideos.length > 0 && (
                <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                        Generated This Session
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {generatedVideos.map((video) => (
                            <div key={video.id} className="border rounded-lg overflow-hidden">
                                {video.output_video_url ? (
                                    <video
                                        src={video.output_video_url}
                                        controls
                                        className="w-full"
                                    />
                                ) : (
                                    <div className="h-48 bg-gray-100 flex items-center justify-center">
                                        <span className="text-gray-400">Processing...</span>
                                    </div>
                                )}
                                <div className="p-4">
                                    <p className="text-sm text-gray-700 line-clamp-2">{video.prompt}</p>
                                    <div className="flex items-center gap-2 mt-2">
                                        {video.mood_category && (
                                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                                {video.mood_category}
                                            </span>
                                        )}
                                        {video.camera_movement && (
                                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                                {video.camera_movement}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
