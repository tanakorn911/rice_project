import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function MarketplaceScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Marketplace</Text>
      <Text>ดูรายการขายพร้อมข้อมูล Sentinel-2 และภาพภาคสนาม</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F7F8F9', padding: 20 },
  heading: { fontSize: 20, fontWeight: '700', marginBottom: 8 },
});
