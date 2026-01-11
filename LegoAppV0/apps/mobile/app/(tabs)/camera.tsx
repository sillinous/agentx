/**
 * Camera Tab - Real camera implementation with Expo Router navigation
 */

import React, { useRef, useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
  ScrollView,
  FlatList,
} from 'react-native';
import { router } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';

type FlashMode = 'off' | 'on' | 'auto';

export default function CameraTab() {
  const cameraRef = useRef<any>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<'front' | 'back'>('back');
  const [flashMode, setFlashMode] = useState<FlashMode>('off');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [detectionResult, setDetectionResult] = useState<any>(null);

  const toggleFlash = () => {
    setFlashMode((current) => {
      if (current === 'off') return 'on';
      if (current === 'on') return 'auto';
      return 'off';
    });
  };

  const switchCamera = () => {
    setFacing((current) => (current === 'back' ? 'front' : 'back'));
  };

  const handleCapture = async () => {
    if (!cameraRef.current || isProcessing) return;

    setIsProcessing(true);

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: false,
      });

      // Simulate detection (replace with real API call)
      setTimeout(() => {
        const mockResult = {
          pieces: [
            { pieceId: '3001', colorId: 'Red', confidence: 0.94, quantity: 3 },
            { pieceId: '3003', colorId: 'Blue', confidence: 0.89, quantity: 2 },
            { pieceId: '3004', colorId: 'Yellow', confidence: 0.92, quantity: 1 },
          ],
          confidenceScore: 0.92,
          processingTimeMs: 1240,
        };
        setDetectionResult(mockResult);
        setShowResults(true);
        setIsProcessing(false);
      }, 2000);
    } catch (error) {
      Alert.alert('Error', 'Failed to capture image. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleRetake = () => {
    setShowResults(false);
    setDetectionResult(null);
  };

  const handleSave = () => {
    Alert.alert(
      'Added to Inventory',
      `${detectionResult?.pieces?.length || 0} pieces added to your collection!`,
      [
        { text: 'Continue Scanning', onPress: handleRetake },
        { text: 'View Inventory', onPress: () => router.push('/inventory') },
      ]
    );
  };

  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionIcon}>◎</Text>
          <Text style={styles.permissionTitle}>Camera Access Needed</Text>
          <Text style={styles.permissionDesc}>
            We need permission to access your camera to detect Lego pieces
          </Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {!showResults && (
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          flash={flashMode}
        >
          {/* Top Controls */}
          <View style={styles.topControls}>
            <View style={styles.spacer} />
            <TouchableOpacity
              style={[styles.flashButton, flashMode === 'on' && styles.flashButtonActive]}
              onPress={toggleFlash}
            >
              <Text style={styles.flashButtonText}>
                {flashMode === 'off' ? '○' : flashMode === 'on' ? '⚡' : '◐'}
              </Text>
              <Text style={styles.flashModeLabel}>
                {flashMode === 'off' ? 'Off' : flashMode === 'on' ? 'On' : 'Auto'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Center Overlay */}
          <View style={styles.centerOverlay}>
            <View style={styles.scanFrame}>
              <View style={[styles.corner, styles.cornerTL]} />
              <View style={[styles.corner, styles.cornerTR]} />
              <View style={[styles.corner, styles.cornerBL]} />
              <View style={[styles.corner, styles.cornerBR]} />
            </View>
            <Text style={styles.overlayText}>Align Lego pieces within the frame</Text>
          </View>

          {/* Bottom Controls */}
          <View style={styles.bottomControls}>
            <TouchableOpacity style={styles.switchButton} onPress={switchCamera} disabled={isProcessing}>
              <Text style={styles.switchButtonText}>↻</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.captureButton, isProcessing && styles.captureButtonDisabled]}
              onPress={handleCapture}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator color="#0066cc" size="small" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            <View style={styles.spacer} />
          </View>
        </CameraView>
      )}

      {/* Results View */}
      {showResults && detectionResult && (
        <ScrollView style={styles.resultsContainer}>
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsTitle}>Detection Results</Text>
            <TouchableOpacity onPress={handleRetake}>
              <Text style={styles.retakeButton}>Retake</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Pieces</Text>
              <Text style={styles.statValue}>{detectionResult.pieces?.length || 0}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Confidence</Text>
              <Text style={styles.statValue}>{(detectionResult.confidenceScore * 100).toFixed(0)}%</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Time</Text>
              <Text style={styles.statValue}>{detectionResult.processingTimeMs}ms</Text>
            </View>
          </View>

          <View style={styles.piecesContainer}>
            <Text style={styles.piecesTitle}>Detected Pieces</Text>
            {detectionResult.pieces?.map((item: any, index: number) => (
              <View key={index} style={styles.pieceItem}>
                <View style={styles.pieceInfo}>
                  <Text style={styles.pieceName}>Piece {item.pieceId}</Text>
                  <View style={styles.pieceDetails}>
                    <Text style={styles.pieceDetail}>Color: {item.colorId}</Text>
                    <Text style={styles.pieceDetail}>Qty: {item.quantity}</Text>
                    <Text style={styles.pieceDetail}>{(item.confidence * 100).toFixed(0)}%</Text>
                  </View>
                </View>
                <View
                  style={[
                    styles.confidenceIndicator,
                    { backgroundColor: item.confidence > 0.8 ? '#4CAF50' : '#FF9800' },
                  ]}
                />
              </View>
            ))}
          </View>

          <View style={styles.actionContainer}>
            <TouchableOpacity style={styles.cancelButton} onPress={handleRetake}>
              <Text style={styles.cancelButtonText}>Retake Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
              <Text style={styles.saveButtonText}>Add to Inventory</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      )}

      {/* Loading Overlay */}
      {isProcessing && !showResults && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingCard}>
            <ActivityIndicator size="large" color="#0066cc" />
            <Text style={styles.loadingTitle}>Analyzing Image</Text>
            <View style={styles.loadingSteps}>
              <View style={styles.loadingStep}>
                <View style={[styles.stepDot, styles.stepDotActive]} />
                <Text style={[styles.stepText, styles.stepTextActive]}>Capturing</Text>
              </View>
              <View style={styles.stepConnector} />
              <View style={styles.loadingStep}>
                <View style={[styles.stepDot, styles.stepDotActive]} />
                <Text style={[styles.stepText, styles.stepTextActive]}>Detecting</Text>
              </View>
              <View style={styles.stepConnector} />
              <View style={styles.loadingStep}>
                <View style={styles.stepDot} />
                <Text style={styles.stepText}>Results</Text>
              </View>
            </View>
            <Text style={styles.loadingHint}>This may take a few seconds...</Text>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
  },
  permissionIcon: {
    fontSize: 64,
    color: '#0066cc',
    marginBottom: 20,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
    textAlign: 'center',
  },
  permissionDesc: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  permissionButton: {
    backgroundColor: '#0066cc',
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 32,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  spacer: {
    width: 44,
  },
  flashButton: {
    minWidth: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 12,
  },
  flashButtonActive: {
    backgroundColor: 'rgba(255,204,0,0.8)',
  },
  flashButtonText: {
    fontSize: 18,
    color: '#fff',
  },
  flashModeLabel: {
    fontSize: 11,
    color: '#fff',
    marginLeft: 4,
    fontWeight: '600',
  },
  centerOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 280,
    height: 280,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#fff',
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderTopLeftRadius: 8,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderTopRightRadius: 8,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderBottomLeftRadius: 8,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderBottomRightRadius: 8,
  },
  overlayText: {
    color: '#fff',
    fontSize: 14,
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 4,
    marginTop: 20,
  },
  bottomControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 20,
    paddingBottom: 40,
  },
  switchButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  switchButtonText: {
    fontSize: 22,
    color: '#fff',
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.5)',
  },
  captureButtonDisabled: {
    opacity: 0.6,
  },
  captureButtonInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#0066cc',
  },
  resultsContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
  },
  retakeButton: {
    fontSize: 14,
    color: '#0066cc',
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  statItem: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 6,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#999',
    marginBottom: 6,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0066cc',
  },
  piecesContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  piecesTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
  },
  pieceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  pieceInfo: {
    flex: 1,
  },
  pieceName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
  },
  pieceDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  pieceDetail: {
    fontSize: 12,
    color: '#999',
    marginRight: 12,
  },
  confidenceIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 12,
  },
  actionContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  cancelButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingVertical: 14,
    marginRight: 12,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#333',
    fontSize: 14,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#0066cc',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    marginHorizontal: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  loadingTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    marginTop: 16,
    marginBottom: 24,
  },
  loadingSteps: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  loadingStep: {
    alignItems: 'center',
  },
  stepDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#ddd',
    marginBottom: 6,
  },
  stepDotActive: {
    backgroundColor: '#0066cc',
  },
  stepText: {
    fontSize: 11,
    color: '#999',
    fontWeight: '500',
  },
  stepTextActive: {
    color: '#0066cc',
  },
  stepConnector: {
    width: 30,
    height: 2,
    backgroundColor: '#ddd',
    marginHorizontal: 8,
    marginBottom: 18,
  },
  loadingHint: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
});
