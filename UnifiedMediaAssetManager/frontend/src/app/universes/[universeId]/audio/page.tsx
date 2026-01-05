'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getUniverseById, Universe } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import AudioProcessor from '@/components/AudioProcessor';

export default function AudioProcessingPage() {
    const params = useParams();
    const { universeId } = params;

    const [universe, setUniverse] = useState<Universe | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
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
                <h1 className="text-4xl font-bold text-gray-900">Audio Processing</h1>
                <p className="text-lg text-gray-600 mt-2">
                    Text-to-speech, transcription, and audio analysis for {universe?.name}
                </p>
            </div>

            {/* Audio Processor Component */}
            <AudioProcessor universeId={universeId as string} />

            {/* Tips Section */}
            <div className="mt-8 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Audio Tips</h2>
                <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-start gap-2">
                        <span className="text-green-500">&#10003;</span>
                        <span><strong>Text-to-Speech:</strong> Generate narration for your story elements and scenes</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-blue-500">&#10003;</span>
                        <span><strong>Transcription:</strong> Convert recorded audio or dialogue to text for editing</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-purple-500">&#10003;</span>
                        <span><strong>Analysis:</strong> Get technical details about audio files for production planning</span>
                    </li>
                </ul>
            </div>
        </div>
    );
}
