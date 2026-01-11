/**
 * Tabs Layout - Main app navigation
 */

import { Tabs } from 'expo-router';
import { Platform, Text, View, StyleSheet } from 'react-native';

function TabBarIcon({ name, color, focused }: { name: string; color: string; focused: boolean }) {
  const icons: Record<string, string> = {
    home: '⌂',
    camera: '◎',
    inventory: '▤',
    search: '⚲',
    profile: '◉',
  };

  return (
    <View style={[styles.iconContainer, focused && styles.iconContainerFocused]}>
      <Text style={[styles.icon, { color }]}>{icons[name] || '●'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconContainerFocused: {
    backgroundColor: 'rgba(0, 102, 204, 0.1)',
  },
  icon: {
    fontSize: 22,
    fontWeight: '600',
  },
});

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#0066cc',
        tabBarInactiveTintColor: '#999',
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#eee',
          paddingTop: 8,
          paddingBottom: Platform.OS === 'ios' ? 24 : 8,
          height: Platform.OS === 'ios' ? 88 : 64,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
        },
        headerStyle: {
          backgroundColor: '#0066cc',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: '600',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused }) => <TabBarIcon name="home" color={color} focused={focused} />,
          headerTitle: 'Lego Vision',
        }}
      />
      <Tabs.Screen
        name="camera"
        options={{
          title: 'Scan',
          tabBarIcon: ({ color, focused }) => <TabBarIcon name="camera" color={color} focused={focused} />,
          headerTitle: 'Scan Bricks',
        }}
      />
      <Tabs.Screen
        name="inventory"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color, focused }) => <TabBarIcon name="inventory" color={color} focused={focused} />,
          headerTitle: 'My Collection',
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: 'Search',
          tabBarIcon: ({ color, focused }) => <TabBarIcon name="search" color={color} focused={focused} />,
          headerTitle: 'Search Pieces',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, focused }) => <TabBarIcon name="profile" color={color} focused={focused} />,
          headerTitle: 'My Profile',
        }}
      />
    </Tabs>
  );
}
