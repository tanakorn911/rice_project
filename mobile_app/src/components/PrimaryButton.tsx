import React from 'react';
import { Pressable, Text, StyleSheet } from 'react-native';

interface Props {
  label: string;
  onPress: () => void;
}

export function PrimaryButton({ label, onPress }: Props) {
  return (
    <Pressable style={styles.button} onPress={onPress}>
      <Text style={styles.text}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#2E7D32',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  text: { color: '#FFFFFF', fontWeight: '600', fontSize: 16 },
});
