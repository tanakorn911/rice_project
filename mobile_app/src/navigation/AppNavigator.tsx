import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { FarmerHomeScreen } from '../screens/FarmerHomeScreen';
import { MarketplaceScreen } from '../screens/MarketplaceScreen';

const Tab = createBottomTabNavigator();

export function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator screenOptions={{ headerShown: false }}>
        <Tab.Screen name="Home" component={FarmerHomeScreen} />
        <Tab.Screen name="Marketplace" component={MarketplaceScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
