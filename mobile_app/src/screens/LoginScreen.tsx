import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { PrimaryButton } from '../components/PrimaryButton';

export function LoginScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>เข้าสู่ระบบ</Text>
      <Text style={styles.subtitle}>ระบบประเมินผลผลิตข้าวด้วย Sentinel-2</Text>
      <PrimaryButton label="เข้าสู่ระบบ" onPress={() => {}} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center', backgroundColor: '#F7F8F9', gap: 12 },
  title: { fontSize: 24, fontWeight: '700', color: '#1B1B1B' },
  subtitle: { fontSize: 14, color: '#5F6368' },
});
