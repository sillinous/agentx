'use client';

import { useState } from 'react';
import { textToSpeech, transcribeAudio, analyzeAudio, AudioJob } from '@/services/api';

interface AudioProcessorProps {
    universeId?: string;
}

type TabType = 'tts' | 'transcribe' | 'analyze';

export function AudioProcessor({ universeId }: AudioProcessorProps) {
    const [activeTab, setActiveTab] = useState<TabType>('tts');

    // TTS State
    const [ttsText, setTtsText] = useState('');
    const [ttsVoice, setTtsVoice] = useState('default');
    const [ttsResult, setTtsResult] = useState<AudioJob | null>(null);
    const [isTtsProcessing, setIsTtsProcessing] = useState(false);

    // Transcribe State
    const [audioUrl, setAudioUrl] = useState('');
    const [transcribeResult, setTranscribeResult] = useState<AudioJob | null>(null);
    const [isTranscribing, setIsTranscribing] = useState(false);

    // Analyze State
    const [analyzeUrl, setAnalyzeUrl] = useState('');
    const [analyzeResult, setAnalyzeResult] = useState<{
        success: boolean;
        analysis?: {
            duration: number;
            format: string;
            sample_rate: number;
            channels: number;
        };
    } | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const [error, setError] = useState<string | null>(null);

    // Voice options
    const voices = [
        { id: 'default', name: 'Default Voice' },
        { id: 'alloy', name: 'Alloy (Neutral)' },
        { id: 'echo', name: 'Echo (Male)' },
        { id: 'fable', name: 'Fable (British)' },
        { id: 'onyx', name: 'Onyx (Deep)' },
        { id: 'nova', name: 'Nova (Female)' },
        { id: 'shimmer', name: 'Shimmer (Soft)' },
    ];

    // Handle TTS
    const handleTts = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!ttsText.trim()) {
            setError('Please enter text to convert');
            return;
        }

        setIsTtsProcessing(true);
        setError(null);
        setTtsResult(null);

        try {
            const result = await textToSpeech({
                text: ttsText,
                voice: ttsVoice,
                universe_id: universeId,
            });
            setTtsResult(result);
        } catch (err) {
            setError('Failed to generate speech');
            console.error(err);
        } finally {
            setIsTtsProcessing(false);
        }
    };

    // Handle Transcription
    const handleTranscribe = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!audioUrl.trim()) {
            setError('Please enter an audio URL');
            return;
        }

        setIsTranscribing(true);
        setError(null);
        setTranscribeResult(null);

        try {
            const result = await transcribeAudio({
                audio_url: audioUrl,
                universe_id: universeId,
            });
            setTranscribeResult(result);
        } catch (err) {
            setError('Failed to transcribe audio');
            console.error(err);
        } finally {
            setIsTranscribing(false);
        }
    };

    // Handle Analysis
    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!analyzeUrl.trim()) {
            setError('Please enter an audio URL');
            return;
        }

        setIsAnalyzing(true);
        setError(null);
        setAnalyzeResult(null);

        try {
            const result = await analyzeAudio({
                audio_url: analyzeUrl,
                universe_id: universeId,
            });
            setAnalyzeResult(result);
        } catch (err) {
            setError('Failed to analyze audio');
            console.error(err);
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-lg">
            {/* Tabs */}
            <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                    {[
                        { id: 'tts', label: 'Text to Speech', icon: '🔊' },
                        { id: 'transcribe', label: 'Transcribe', icon: '📝' },
                        { id: 'analyze', label: 'Analyze', icon: '📊' },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => {
                                setActiveTab(tab.id as TabType);
                                setError(null);
                            }}
                            className={`flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm transition-colors ${
                                activeTab === tab.id
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            <span className="mr-2">{tab.icon}</span>
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </div>

            <div className="p-6">
                {/* Error Display */}
                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
                        {error}
                    </div>
                )}

                {/* TTS Tab */}
                {activeTab === 'tts' && (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">
                            Convert Text to Speech
                        </h3>
                        <form onSubmit={handleTts} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Text
                                </label>
                                <textarea
                                    value={ttsText}
                                    onChange={(e) => setTtsText(e.target.value)}
                                    rows={4}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="Enter text to convert to speech..."
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Voice
                                </label>
                                <select
                                    value={ttsVoice}
                                    onChange={(e) => setTtsVoice(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                                >
                                    {voices.map((voice) => (
                                        <option key={voice.id} value={voice.id}>
                                            {voice.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <button
                                type="submit"
                                disabled={isTtsProcessing || !ttsText.trim()}
                                className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {isTtsProcessing ? 'Generating...' : 'Generate Speech'}
                            </button>
                        </form>

                        {/* TTS Result */}
                        {ttsResult && (
                            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                <h4 className="text-sm font-medium text-gray-700 mb-2">Result</h4>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                        ttsResult.status === 'completed'
                                            ? 'bg-green-100 text-green-800'
                                            : ttsResult.status === 'failed'
                                            ? 'bg-red-100 text-red-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {ttsResult.status}
                                    </span>
                                </div>
                                {ttsResult.result?.audio_url && (
                                    <audio
                                        src={ttsResult.result.audio_url}
                                        controls
                                        className="w-full mt-2"
                                    />
                                )}
                                {ttsResult.result?.duration && (
                                    <p className="text-xs text-gray-500 mt-2">
                                        Duration: {ttsResult.result.duration.toFixed(1)}s
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Transcribe Tab */}
                {activeTab === 'transcribe' && (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">
                            Transcribe Audio
                        </h3>
                        <form onSubmit={handleTranscribe} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Audio URL
                                </label>
                                <input
                                    type="url"
                                    value={audioUrl}
                                    onChange={(e) => setAudioUrl(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="https://example.com/audio.mp3"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={isTranscribing || !audioUrl.trim()}
                                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {isTranscribing ? 'Transcribing...' : 'Transcribe Audio'}
                            </button>
                        </form>

                        {/* Transcription Result */}
                        {transcribeResult && (
                            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                <h4 className="text-sm font-medium text-gray-700 mb-2">Transcription</h4>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                        transcribeResult.status === 'completed'
                                            ? 'bg-green-100 text-green-800'
                                            : transcribeResult.status === 'failed'
                                            ? 'bg-red-100 text-red-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {transcribeResult.status}
                                    </span>
                                </div>
                                {transcribeResult.result?.transcription && (
                                    <div className="mt-2 p-3 bg-white border rounded-md">
                                        <p className="text-gray-700 whitespace-pre-wrap">
                                            {transcribeResult.result.transcription}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Analyze Tab */}
                {activeTab === 'analyze' && (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">
                            Analyze Audio
                        </h3>
                        <form onSubmit={handleAnalyze} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Audio URL
                                </label>
                                <input
                                    type="url"
                                    value={analyzeUrl}
                                    onChange={(e) => setAnalyzeUrl(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="https://example.com/audio.mp3"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={isAnalyzing || !analyzeUrl.trim()}
                                className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {isAnalyzing ? 'Analyzing...' : 'Analyze Audio'}
                            </button>
                        </form>

                        {/* Analysis Result */}
                        {analyzeResult && analyzeResult.analysis && (
                            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                <h4 className="text-sm font-medium text-gray-700 mb-3">Analysis Results</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-3 bg-white rounded-md border">
                                        <p className="text-xs text-gray-500">Duration</p>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {analyzeResult.analysis.duration.toFixed(2)}s
                                        </p>
                                    </div>
                                    <div className="p-3 bg-white rounded-md border">
                                        <p className="text-xs text-gray-500">Format</p>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {analyzeResult.analysis.format}
                                        </p>
                                    </div>
                                    <div className="p-3 bg-white rounded-md border">
                                        <p className="text-xs text-gray-500">Sample Rate</p>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {analyzeResult.analysis.sample_rate} Hz
                                        </p>
                                    </div>
                                    <div className="p-3 bg-white rounded-md border">
                                        <p className="text-xs text-gray-500">Channels</p>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {analyzeResult.analysis.channels === 1 ? 'Mono' : 'Stereo'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default AudioProcessor;
