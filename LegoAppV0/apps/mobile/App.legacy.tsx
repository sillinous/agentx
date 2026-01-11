/**
 * Lego Vision Mobile App
 * Main entry point for React Native/Expo application
 */

import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ApolloClient, InMemoryCache, HttpLink, ApolloProvider } from '@apollo/client';
import { AuthContext } from './src/context/AuthContext';
import { useAuth } from './src/hooks/useAuth';

// Screens
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/auth/LoginScreen';
import RegisterScreen from './src/screens/auth/RegisterScreen';
import HomeScreen from './src/screens/HomeScreen';
import CameraScreen from './src/screens/camera/CameraScreen';
import InventoryScreen from './src/screens/inventory/InventoryScreen';
import SearchScreen from './src/screens/search/SearchScreen';
import ProfileScreen from './src/screens/profile/ProfileScreen';

const Stack = createNativeStackNavigator();

/**
 * Initialize Apollo Client for GraphQL
 */
function createApolloClient(token: string | null) {
  return new ApolloClient({
    ssrMode: false,
    link: new HttpLink({
      uri: process.env.EXPO_PUBLIC_GRAPHQL_ENDPOINT || 'http://localhost:4000/graphql',
      credentials: 'include',
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    }),
    cache: new InMemoryCache(),
  });
}

/**
 * Root Navigation Component
 */
function RootNavigator() {
  const { state, dispatch } = React.useContext(AuthContext);
  const [apolloClient, setApolloClient] = useState(createApolloClient(state.userToken));

  useEffect(() => {
    // Update Apollo client when token changes
    setApolloClient(createApolloClient(state.userToken));
  }, [state.userToken]);

  if (state.isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#0066cc" />
      </View>
    );
  }

  return (
    <ApolloProvider client={apolloClient}>
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: true,
            headerStyle: {
              backgroundColor: '#f8f8f8',
              elevation: 0,
              shadowOpacity: 0,
              borderBottomWidth: 1,
              borderBottomColor: '#e0e0e0',
            },
            headerTintColor: '#0066cc',
            headerTitleStyle: {
              fontWeight: '600',
              fontSize: 18,
            },
          }}
        >
          {state.userToken == null ? (
            // Auth Stack
            <Stack.Group
              screenOptions={{
                headerShown: false,
              }}
            >
              <Stack.Screen name="Login" component={LoginScreen} />
              <Stack.Screen name="Register" component={RegisterScreen} />
            </Stack.Group>
          ) : (
            // App Stack
            <Stack.Group>
              <Stack.Screen
                name="Home"
                component={HomeScreen}
                options={{
                  title: 'Lego Vision',
                }}
              />
              <Stack.Screen
                name="Camera"
                component={CameraScreen}
                options={{
                  title: 'Scan Lego',
                  headerBackTitle: 'Back',
                }}
              />
              <Stack.Screen
                name="Inventory"
                component={InventoryScreen}
                options={{
                  title: 'My Inventory',
                }}
              />
              <Stack.Screen
                name="Search"
                component={SearchScreen}
                options={{
                  title: 'Search Pieces',
                }}
              />
              <Stack.Screen
                name="Profile"
                component={ProfileScreen}
                options={{
                  title: 'Profile',
                }}
              />
            </Stack.Group>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </ApolloProvider>
  );
}

/**
 * App Entry Point
 */
export default function App() {
  const [state, dispatch] = React.useReducer(authReducer, initialState);

  React.useEffect(() => {
    const bootstrapAsync = async () => {
      let userToken;
      try {
        // Restore token on app launch
        // userToken = await AsyncStorage.getItem('userToken');
      } catch (e) {
        console.error('Failed to restore session:', e);
      }

      dispatch({ type: 'RESTORE_TOKEN', token: userToken });
    };

    bootstrapAsync();
  }, []);

  return (
    <AuthContext.Provider value={{ state, dispatch }}>
      <RootNavigator />
    </AuthContext.Provider>
  );
}

// Auth reducer for managing auth state
const initialState = {
  isLoading: true,
  isSignout: false,
  userToken: null,
  user: null,
};

function authReducer(state: any, action: any) {
  switch (action.type) {
    case 'RESTORE_TOKEN':
      return {
        ...state,
        userToken: action.token,
        isLoading: false,
      };
    case 'SIGN_IN':
      return {
        ...state,
        isSignout: false,
        userToken: action.token,
        user: action.user,
      };
    case 'SIGN_UP':
      return {
        ...state,
        isSignout: false,
        userToken: action.token,
        user: action.user,
      };
    case 'SIGN_OUT':
      return {
        ...state,
        isSignout: true,
        userToken: null,
        user: null,
      };
    default:
      return state;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});
