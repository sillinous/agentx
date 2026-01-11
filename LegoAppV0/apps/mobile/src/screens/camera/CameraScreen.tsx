/**
 * CameraScreen
 * Handles Lego piece detection using camera and vision AI
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
  Modal,
  FlatList,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useCamera } from '../../hooks/useCamera';

type RootStackParamList = {
  Camera: undefined;
  Home: undefined;
};

type CameraScreenProps = NativeStackScreenProps<RootStackParamList, 'Camera'>;

/**
 * CameraScreen Component
 */
export default function CameraScreen({ navigation }: CameraScreenProps) {
  const cameraRef = useRef<any>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const {
    facing,
    flashMode,
    takePicture,
    detectPieces,
    toggleFlash,
    switchCamera,
    detectionState,
    isSubmittingDetection,
  } = useCamera();

  const [showResults, setShowResults] = useState(false);
  const [scannedImage, setScannedImage] = useState<string | null>(null);

  /**
   * Request camera permission if not granted
   */
  React.useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, [permission]);

  /**
   * Handle camera capture and detection
   */
  const handleCapture = async () => {
    try {
      const photoUri = await takePicture();
      if (photoUri) {
        setScannedImage(photoUri);

        // In production, would convert to base64 and run inference
        const result = await detectPieces('');

        if (result) {
          setShowResults(true);
        } else if (detectionState.error) {
          Alert.alert('Detection Failed', detectionState.error);
        }
      } else if (detectionState.error) {
        Alert.alert('Camera Error', detectionState.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to capture image');
    }
  };

  /**
   * Handle retake photo
   */
  const handleRetake = () => {
    setScannedImage(null);
    setShowResults(false);
    detectionState.detectionResult && setShowResults(false);
  };

  /**
   * Handle save detection to inventory
   */
  const handleSave = () => {
    Alert.alert(
      'Success',
      `${detectionState.detectionResult?.pieces?.length || 0} pieces added to inventory`,
      [
        {
          text: 'Continue Scanning',
          onPress: handleRetake,
        },
        {
          text: 'Go to Inventory',
          onPress: () => {
            navigation.navigate('Home');
          },
        },
      ]
    );
  };

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionIcon}>📷</Text>
          <Text style={styles.permissionTitle}>Camera Access Needed</Text>
          <Text style={styles.permissionDesc}>
            We need permission to access your camera to detect Lego pieces
          </Text>
          <TouchableOpacity
            style={styles.permissionButton}
            onPress={requestPermission}
          >
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Camera View */}
      {!showResults && (
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          flash={flashMode}
        >
          {/* Top Controls */}
          <View style={styles.topControls}>
            <TouchableOpacity style={styles.closeButton} onPress={() => navigation.goBack()}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.flashButton,
                flashMode === 'on' && styles.flashButtonActive
              ]}
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
            <Text style={styles.overlayText}>Align Lego pieces within the frame</Text>
          </View>

          {/* Bottom Controls */}
          <View style={styles.bottomControls}>
            <TouchableOpacity
              style={styles.switchButton}
              onPress={switchCamera}
              disabled={isSubmittingDetection}
            >
              <Text style={styles.switchButtonText}>🔄</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.captureButton,
                isSubmittingDetection && styles.captureButtonDisabled,
              ]}
              onPress={handleCapture}
              disabled={isSubmittingDetection}
            >
              {isSubmittingDetection ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            <View style={styles.spacer} />
          </View>
        </CameraView>
      )}

      {/* Results Modal */}
      {showResults && detectionState.detectionResult && (
        <ScrollView style={styles.resultsContainer}>
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsTitle}>Detection Results</Text>
            <TouchableOpacity onPress={handleRetake}>
              <Text style={styles.retakeButton}>Retake</Text>
            </TouchableOpacity>
          </View>

          {/* Detection Stats */}
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Pieces Detected</Text>
              <Text style={styles.statValue}>
                {detectionState.detectionResult.pieces?.length || 0}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Confidence</Text>
              <Text style={styles.statValue}>
                {(detectionState.detectionResult.confidenceScore * 100).toFixed(0)}%
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Processing</Text>
              <Text style={styles.statValue}>
                {detectionState.detectionResult.processingTimeMs}ms
              </Text>
            </View>
          </View>

          {/* Detected Pieces List */}
          {detectionState.detectionResult.pieces && (
            <View style={styles.piecesContainer}>
              <Text style={styles.piecesTitle}>Detected Pieces</Text>
              <FlatList
                scrollEnabled={false}
                data={detectionState.detectionResult.pieces}
                keyExtractor={(item, index) => `${item.pieceId}-${index}`}
                renderItem={({ item }) => (
                  <View style={styles.pieceItem}>
                    <View style={styles.pieceInfo}>
                      <Text style={styles.pieceName}>Piece {item.pieceId}</Text>
                      <View style={styles.pieceDetails}>
                        <Text style={styles.pieceDetail}>
                          Color: {item.colorId}
                        </Text>
                        <Text style={styles.pieceDetail}>
                          Confidence: {(item.confidence * 100).toFixed(0)}%
                        </Text>
                        {item.isInferred && (
                          <Text style={styles.pieceDetail}>Inferred</Text>
                        )}
                      </View>
                    </View>
                    <View
                      style={[
                        styles.confidenceIndicator,
                        {
                          backgroundColor: item.confidence > 0.8 ? '#4CAF50' : '#FF9800',
                        },
                      ]}
                    />
                  </View>
                )}
              />
            </View>
          )}

          {/* Error Display */}
          {detectionState.error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{detectionState.error}</Text>
            </View>
          )}

          {/* Action Buttons */}
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

      {/* Loading State with Progress Steps */}
      {isSubmittingDetection && !showResults && (
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
  },
  permissionButton: {
    backgroundColor: '#0066cc',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 32,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  closeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 20,
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
  overlayText: {
    color: '#fff',
    fontSize: 14,
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 4,
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
    fontSize: 18,
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
  spacer: {
    width: 44,
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
  errorContainer: {
    backgroundColor: '#fee',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 20,
    marginVertical: 16,
  },
  errorText: {
    color: '#c33',
    fontSize: 12,
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
    paddingVertical: 12,
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
    paddingVertical: 12,
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
