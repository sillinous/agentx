'use client';

import { useState, useEffect, useCallback } from 'react';
import {
    generateVideo,
    listVideoJobs,
    getVideoJob,
    generateVideoStrategy,
    VideoJob,
    VideoStrategyVariation,
} from '@/services/api';

interface VideoGeneratorProps {
    universeId?: string;
    onVideoGenerated?: (job: VideoJob) => void;
}

export function VideoGenerator({ universeId, onVideoGenerated }: VideoGeneratorProps) {
    // Form state
    const [prompt, setPrompt] = useState('');
    const [mood, setMood] = useState(50);
    const [aspectRatio, setAspectRatio] = useState('16:9');
    const [duration, setDuration] = useState(5);
    const [negativePrompt, setNegativePrompt] = useState('');

    // Strategy preview
    const [strategies, setStrategies] = useState<VideoStrategyVariation[]>([]);
    const [selectedStrategy, setSelectedStrategy] = useState<VideoStrategyVariation | null>(null);
    const [isGeneratingStrategy, setIsGeneratingStrategy] = useState(false);

    // Job management
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [currentJob, setCurrentJob] = useState<VideoJob | null>(null);
    const [recentJobs, setRecentJobs] = useState<VideoJob[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Mood category labels
    const getMoodLabel = (value: number) => {
        if (value < 25) return 'Calm / Intimate';
        if (value < 50) return 'Balanced / Storytelling';
        if (value < 75) return 'Dynamic / Energetic';
        return 'High Energy / Intense';
    };

    // Generate strategy preview
    const handlePreviewStrategy = async () => {
        if (!prompt.trim()) {
            setError('Please enter a prompt first');
            return;
        }

        setIsGeneratingStrategy(true);
        setError(null);
        setStrategies([]);

        try {
            const result = await generateVideoStrategy({
                prompt,
                mood,
                num_variations: 3,
            });

            if (result.success && result.variations) {
                setStrategies(result.variations);
                setSelectedStrategy(result.variations[0]);
            }
        } catch (err) {
            setError('Failed to generate strategy preview');
            console.error(err);
        } finally {
            setIsGeneratingStrategy(false);
        }
    };

    // Submit video generation
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim()) {
            setError('Prompt is required');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const result = await generateVideo({
                universe_id: universeId,
                prompt: selectedStrategy?.enriched_prompt || prompt,
                mood,
                aspect_ratio: aspectRatio,
                duration,
                negative_prompt: negativePrompt || undefined,
            });

            setCurrentJobId(result.job_id);
            setCurrentJob({
                id: result.job_id,
                status: result.status,
                prompt,
                generation_type: 'text_to_video',
                mood_category: result.strategy.mood_category,
                camera_movement: result.strategy.camera_movement,
            });
        } catch (err) {
            setError('Failed to start video generation');
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    // Poll for job status
    const pollJobStatus = useCallback(async () => {
        if (!currentJobId) return;

        const job = await getVideoJob(currentJobId);
        if (job) {
            setCurrentJob(job);

            if (job.status === 'completed' || job.status === 'failed') {
                // Stop polling, refresh recent jobs
                setCurrentJobId(null);
                if (job.status === 'completed' && onVideoGenerated) {
                    onVideoGenerated(job);
                }
                loadRecentJobs();
            }
        }
    }, [currentJobId, onVideoGenerated]);

    // Load recent jobs
    const loadRecentJobs = async () => {
        const result = await listVideoJobs({
            universe_id: universeId,
            limit: 5,
        });
        setRecentJobs(result.jobs);
    };

    // Poll job status while processing
    useEffect(() => {
        if (currentJobId && currentJob?.status === 'processing') {
            const interval = setInterval(pollJobStatus, 3000);
            return () => clearInterval(interval);
        }
    }, [currentJobId, currentJob?.status, pollJobStatus]);

    // Load recent jobs on mount
    useEffect(() => {
        loadRecentJobs();
    }, [universeId]);

    return (
        <div className="space-y-6">
            {/* Generation Form */}
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Video Generation</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Prompt */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Prompt
                        </label>
                        <textarea
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            rows={3}
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Describe the video you want to generate..."
                        />
                    </div>

                    {/* Mood Slider */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Mood: {getMoodLabel(mood)} ({mood})
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={mood}
                            onChange={(e) => setMood(Number(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>Calm</span>
                            <span>Balanced</span>
                            <span>Dynamic</span>
                            <span>Intense</span>
                        </div>
                    </div>

                    {/* Settings Row */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Aspect Ratio
                            </label>
                            <select
                                value={aspectRatio}
                                onChange={(e) => setAspectRatio(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value="16:9">16:9 (Landscape)</option>
                                <option value="9:16">9:16 (Portrait)</option>
                                <option value="1:1">1:1 (Square)</option>
                                <option value="4:3">4:3 (Standard)</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Duration (seconds)
                            </label>
                            <select
                                value={duration}
                                onChange={(e) => setDuration(Number(e.target.value))}
                                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value={3}>3 seconds</option>
                                <option value={5}>5 seconds</option>
                                <option value={10}>10 seconds</option>
                            </select>
                        </div>
                    </div>

                    {/* Negative Prompt (Advanced) */}
                    <details className="group">
                        <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900">
                            Advanced Options
                        </summary>
                        <div className="mt-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Negative Prompt
                            </label>
                            <input
                                type="text"
                                value={negativePrompt}
                                onChange={(e) => setNegativePrompt(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                                placeholder="Things to avoid in the video..."
                            />
                        </div>
                    </details>

                    {/* Strategy Preview Button */}
                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={handlePreviewStrategy}
                            disabled={isGeneratingStrategy || !prompt.trim()}
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isGeneratingStrategy ? 'Generating...' : 'Preview Strategies'}
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting || !prompt.trim()}
                            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isSubmitting ? 'Starting Generation...' : 'Generate Video'}
                        </button>
                    </div>
                </form>

                {error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
                        {error}
                    </div>
                )}
            </div>

            {/* Strategy Variations */}
            {strategies.length > 0 && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Variations</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {strategies.map((strategy, index) => (
                            <div
                                key={index}
                                onClick={() => setSelectedStrategy(strategy)}
                                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                                    selectedStrategy === strategy
                                        ? 'border-indigo-500 bg-indigo-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
                            >
                                <div className="text-sm font-medium text-gray-900 mb-2">
                                    {strategy.mood_category}
                                </div>
                                <div className="text-xs text-gray-500 space-y-1">
                                    <p><span className="font-medium">Camera:</span> {strategy.camera_movement}</p>
                                    <p><span className="font-medium">Pacing:</span> {strategy.pacing}</p>
                                    <p><span className="font-medium">Lighting:</span> {strategy.lighting}</p>
                                </div>
                                <p className="mt-2 text-xs text-gray-600 line-clamp-2">
                                    {strategy.enriched_prompt}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current Job Status */}
            {currentJob && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Job</h3>
                    <JobStatusCard job={currentJob} />
                </div>
            )}

            {/* Recent Jobs */}
            {recentJobs.length > 0 && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Jobs</h3>
                    <div className="space-y-3">
                        {recentJobs.map((job) => (
                            <JobStatusCard key={job.id} job={job} compact />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// Job Status Card Component
function JobStatusCard({ job, compact = false }: { job: VideoJob; compact?: boolean }) {
    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        processing: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
    };

    return (
        <div className={`p-4 border rounded-lg ${compact ? 'border-gray-100' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[job.status] || 'bg-gray-100'}`}>
                    {job.status}
                </span>
                {job.mood_category && (
                    <span className="text-xs text-gray-500">{job.mood_category}</span>
                )}
            </div>

            <p className={`text-gray-700 ${compact ? 'text-sm line-clamp-1' : ''}`}>
                {job.prompt}
            </p>

            {job.status === 'processing' && (
                <div className="mt-3 flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm text-blue-600">Processing...</span>
                </div>
            )}

            {job.status === 'completed' && job.output_video_url && (
                <div className="mt-3">
                    <video
                        src={job.output_video_url}
                        controls
                        className="w-full rounded-md"
                        style={{ maxHeight: compact ? '150px' : '300px' }}
                    />
                </div>
            )}

            {job.status === 'failed' && job.error_message && (
                <p className="mt-2 text-sm text-red-600">{job.error_message}</p>
            )}

            {!compact && job.created_at && (
                <p className="mt-2 text-xs text-gray-400">
                    Created: {new Date(job.created_at).toLocaleString()}
                </p>
            )}
        </div>
    );
}

export default VideoGenerator;
