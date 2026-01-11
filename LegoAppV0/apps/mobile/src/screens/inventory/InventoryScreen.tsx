/**
 * InventoryScreen
 * Displays user's Lego piece inventory with filtering and management
 */

import React, { useState, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  TextInput,
  Modal,
  Alert,
  RefreshControl,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_USER_INVENTORY_QUERY,
  UPDATE_INVENTORY_MUTATION,
  REMOVE_FROM_INVENTORY_MUTATION,
} from '../../queries/operations';

type RootStackParamList = {
  Inventory: undefined;
  Home: undefined;
};

type InventoryScreenProps = NativeStackScreenProps<RootStackParamList, 'Inventory'>;

/**
 * InventoryScreen Component
 */
export default function InventoryScreen({ navigation }: InventoryScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'quantity' | 'date'>('name');
  const [editingItem, setEditingItem] = useState<any | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editedQuantity, setEditedQuantity] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch inventory
  const { data, loading, error, refetch } = useQuery(GET_USER_INVENTORY_QUERY, {
    variables: { limit: 100, offset: 0 },
  });

  // Mutations
  const [updateInventory] = useMutation(UPDATE_INVENTORY_MUTATION);
  const [removeFromInventory] = useMutation(REMOVE_FROM_INVENTORY_MUTATION);

  /**
   * Handle pull-to-refresh
   */
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  /**
   * Filter inventory based on search query
   */
  const filteredItems = (data?.getUserInventory?.inventoryItems || []).filter((item: any) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      item.piece?.name?.toLowerCase().includes(searchLower) ||
      item.piece?.number?.toLowerCase().includes(searchLower) ||
      item.color?.name?.toLowerCase().includes(searchLower)
    );
  });

  /**
   * Sort inventory
   */
  const sortedItems = [...filteredItems].sort((a: any, b: any) => {
    switch (sortBy) {
      case 'quantity':
        return (b.quantity || 0) - (a.quantity || 0);
      case 'date':
        return new Date(b.addedAt).getTime() - new Date(a.addedAt).getTime();
      case 'name':
      default:
        return (a.piece?.name || '').localeCompare(b.piece?.name || '');
    }
  });

  /**
   * Handle edit item
   */
  const handleEditItem = (item: any) => {
    setEditingItem(item);
    setEditedQuantity(item.quantity.toString());
    setShowEditModal(true);
  };

  /**
   * Handle save edited item
   */
  const handleSaveEdit = async () => {
    if (!editingItem || !editedQuantity) return;

    const quantity = parseInt(editedQuantity, 10);
    if (isNaN(quantity) || quantity < 0) {
      Alert.alert('Invalid Quantity', 'Please enter a valid positive number');
      return;
    }

    setIsSaving(true);
    try {
      await updateInventory({
        variables: {
          id: editingItem.id,
          quantity,
        },
      });

      setShowEditModal(false);
      setEditingItem(null);
      refetch();
      Alert.alert('Saved', `Updated quantity to ${quantity}`);
    } catch (err: any) {
      const message = err?.message?.includes('network')
        ? 'Network error. Check your connection and try again.'
        : 'Unable to update inventory. Please try again.';
      Alert.alert('Update Failed', message);
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle delete item
   */
  const handleDeleteItem = (item: any) => {
    Alert.alert(
      'Delete Item',
      `Remove ${item.piece?.name} from inventory?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await removeFromInventory({
                variables: { id: item.id },
              });
              refetch();
              Alert.alert('Success', 'Item removed from inventory');
            } catch (err) {
              Alert.alert('Error', 'Failed to delete item');
            }
          },
        },
      ]
    );
  };

  /**
   * Render inventory item
   */
  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.itemCard}>
      <View style={styles.itemImage}>
        <Text style={styles.imageIcon}>🧱</Text>
      </View>
      <View style={styles.itemContent}>
        <Text style={styles.itemName}>{item.piece?.name || 'Unknown'}</Text>
        <View style={styles.itemMeta}>
          <Text style={styles.itemMetaText}>{item.piece?.number}</Text>
          <Text style={styles.itemMetaDot}>•</Text>
          <Text style={styles.itemMetaText}>{item.color?.name || 'Unknown'}</Text>
        </View>
        <Text style={styles.itemCondition}>
          {item.condition === 'N' ? 'New' : 'Used'} • Qty: {item.quantity}
        </Text>
      </View>
      <View style={styles.itemActions}>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => handleEditItem(item)}
        >
          <Text style={styles.editButtonText}>✏️</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDeleteItem(item)}
        >
          <Text style={styles.deleteButtonText}>🗑️</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Inventory</Text>
        <Text style={styles.headerSubtitle}>
          {data?.getUserInventory?.totalCount || 0} pieces
        </Text>
      </View>

      {/* Search and Filter */}
      <View style={styles.filterContainer}>
        <View style={styles.searchInputContainer}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Search pieces..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#999"
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={styles.clearIcon}>✕</Text>
            </TouchableOpacity>
          ) : null}
        </View>

        {/* Sort Options */}
        <View style={styles.sortContainer}>
          {(['name', 'quantity', 'date'] as const).map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.sortButton,
                sortBy === option && styles.sortButtonActive,
              ]}
              onPress={() => setSortBy(option)}
            >
              <Text
                style={[
                  styles.sortButtonText,
                  sortBy === option && styles.sortButtonTextActive,
                ]}
              >
                {option === 'name' ? 'A-Z' : option === 'quantity' ? 'Qty' : 'Date'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Inventory List */}
      {loading && !refreshing ? (
        <View style={styles.skeletonContainer}>
          {[1, 2, 3, 4, 5].map((i) => (
            <View key={i} style={styles.skeletonCard}>
              <View style={styles.skeletonImage} />
              <View style={styles.skeletonContent}>
                <View style={styles.skeletonTitle} />
                <View style={styles.skeletonMeta} />
                <View style={styles.skeletonCondition} />
              </View>
            </View>
          ))}
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Couldn't Load Inventory</Text>
          <Text style={styles.errorDesc}>
            {error.message?.includes('network')
              ? 'Check your internet connection and try again.'
              : 'Something went wrong. Please try again.'}
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : sortedItems.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>📦</Text>
          <Text style={styles.emptyTitle}>No items in inventory</Text>
          <Text style={styles.emptyDesc}>
            Scan Lego pieces to add them to your inventory
          </Text>
        </View>
      ) : (
        <FlatList
          data={sortedItems}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor="#0066cc"
              colors={['#0066cc']}
            />
          }
          removeClippedSubviews={true}
          maxToRenderPerBatch={10}
          initialNumToRender={10}
        />
      )}

      {/* Edit Modal */}
      <Modal
        visible={showEditModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowEditModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Edit Quantity</Text>
              <TouchableOpacity onPress={() => setShowEditModal(false)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalLabel}>
              {editingItem?.piece?.name || 'Unknown'}
            </Text>

            <TextInput
              style={styles.quantityInput}
              placeholder="Quantity"
              keyboardType="number-pad"
              value={editedQuantity}
              onChangeText={setEditedQuantity}
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowEditModal(false)}
                disabled={isSaving}
              >
                <Text style={styles.modalCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalSaveButton, isSaving && styles.modalSaveButtonDisabled]}
                onPress={handleSaveEdit}
                disabled={isSaving}
              >
                {isSaving ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.modalSaveButtonText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#999',
  },
  filterContainer: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginBottom: 12,
    paddingHorizontal: 12,
  },
  searchIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    height: 40,
    color: '#333',
    fontSize: 14,
  },
  clearIcon: {
    fontSize: 16,
    color: '#999',
  },
  sortContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  sortButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
  },
  sortButtonActive: {
    backgroundColor: '#0066cc',
  },
  sortButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#999',
  },
  sortButtonTextActive: {
    color: '#fff',
  },
  listContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  itemImage: {
    width: 50,
    height: 50,
    borderRadius: 8,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  imageIcon: {
    fontSize: 24,
  },
  itemContent: {
    flex: 1,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  itemMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  itemMetaText: {
    fontSize: 12,
    color: '#999',
  },
  itemMetaDot: {
    marginHorizontal: 6,
    color: '#ddd',
  },
  itemCondition: {
    fontSize: 11,
    color: '#0066cc',
    fontWeight: '500',
  },
  itemActions: {
    flexDirection: 'row',
    gap: 8,
  },
  editButton: {
    width: 32,
    height: 32,
    borderRadius: 6,
    backgroundColor: '#f0f4ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  editButtonText: {
    fontSize: 16,
  },
  deleteButton: {
    width: 32,
    height: 32,
    borderRadius: 6,
    backgroundColor: '#ffe0e0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 16,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  skeletonContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  skeletonCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    alignItems: 'center',
  },
  skeletonImage: {
    width: 50,
    height: 50,
    borderRadius: 8,
    backgroundColor: '#e8e8e8',
    marginRight: 12,
  },
  skeletonContent: {
    flex: 1,
  },
  skeletonTitle: {
    width: '70%',
    height: 14,
    borderRadius: 4,
    backgroundColor: '#e8e8e8',
    marginBottom: 8,
  },
  skeletonMeta: {
    width: '50%',
    height: 10,
    borderRadius: 4,
    backgroundColor: '#e8e8e8',
    marginBottom: 6,
  },
  skeletonCondition: {
    width: '30%',
    height: 10,
    borderRadius: 4,
    backgroundColor: '#e8e8e8',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorDesc: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  retryButton: {
    backgroundColor: '#0066cc',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
  },
  emptyDesc: {
    fontSize: 13,
    color: '#999',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
  },
  modalCloseText: {
    fontSize: 20,
    color: '#999',
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  quantityInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 20,
    color: '#333',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  modalCancelButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  modalSaveButton: {
    flex: 1,
    backgroundColor: '#0066cc',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  modalSaveButtonDisabled: {
    opacity: 0.7,
  },
  modalSaveButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
