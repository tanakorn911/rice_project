import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function FarmerHomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Farmer Home</Text>
      <Text style={styles.text}>Verification status, latest field analysis, my listings, and notifications.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F7F8F9', padding: 20 },
  heading: { fontSize: 20, fontWeight: '700', marginBottom: 8 },
  text: { color: '#444' },
});
