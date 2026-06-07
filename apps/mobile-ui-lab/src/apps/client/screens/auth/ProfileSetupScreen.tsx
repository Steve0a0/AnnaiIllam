import { useState } from 'react';
import {
  Alert,
  Dimensions,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../../../shared/store/auth.store';
import { clientProfileService } from '../../../../shared/services/client-profile.service';
import { authStorage } from '../../../../shared/lib/auth-storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { ClientAuthStackParamList } from '../../navigation/types';

const { width } = Dimensions.get('window');

type ClientType = 'individual' | 'company';

type Props = {
  navigation: NativeStackNavigationProp<ClientAuthStackParamList, 'ProfileSetup'>;
};

type Envelope<T> = { success: boolean; message: string; data: T };

export default function ProfileSetupScreen(_props: Props) {
  const { user, setProfileComplete } = useAuthStore();

  const [clientType, setClientType] = useState<ClientType>('individual');
  const [contactName, setContactName] = useState(user?.name ?? '');
  const [companyName, setCompanyName] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [email, setEmail] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [focused, setFocused] = useState<string | null>(null);

  const handleSave = async () => {
    if (!contactName.trim()) {
      Alert.alert('Missing name', 'Please enter your name to continue.');
      return;
    }
    if (clientType === 'company' && !companyName.trim()) {
      Alert.alert('Missing company name', 'Please enter your company name.');
      return;
    }
    if (!city.trim()) {
      Alert.alert('Missing city', 'Please enter your city.');
      return;
    }
    if (!state.trim()) {
      Alert.alert('Missing state', 'Please enter your state.');
      return;
    }
    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      Alert.alert('Invalid email', 'Please enter a valid email address or leave it blank.');
      return;
    }

    setIsSaving(true);
    try {
      await clientProfileService.createProfile({
        client_type: clientType,
        company_name: clientType === 'company' ? companyName.trim() : null,
        contact_name: contactName.trim(),
        city: city.trim(),
        state: state.trim(),
        email: email.trim() || null,
      });
      await authStorage.setIsProfileComplete(true);
      setProfileComplete(true);
    } catch {
      Alert.alert('Save failed', 'Could not save your profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const inputStyle = (field: string) => [
    styles.input,
    focused === field && styles.inputFocused,
  ];

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.blobTopRight} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.stepBadge}>
            <Text style={styles.stepBadgeText}>Step 2 of 2</Text>
          </View>
          <Text style={styles.heading}>Almost there!</Text>
          <Text style={styles.subheading}>
            Tell us a bit about yourself so we can find the right workers for you.
          </Text>
        </View>

        {/* Client type toggle */}
        <View style={styles.fieldGroup}>
          <Text style={styles.label}>I am a</Text>
          <View style={styles.toggle}>
            <Pressable
              style={[styles.toggleOption, clientType === 'individual' && styles.toggleActive]}
              onPress={() => setClientType('individual')}
            >
              <Text style={[styles.toggleText, clientType === 'individual' && styles.toggleTextActive]}>
                Individual
              </Text>
            </Pressable>
            <Pressable
              style={[styles.toggleOption, clientType === 'company' && styles.toggleActive]}
              onPress={() => setClientType('company')}
            >
              <Text style={[styles.toggleText, clientType === 'company' && styles.toggleTextActive]}>
                Company
              </Text>
            </Pressable>
          </View>
        </View>

        {/* Company name — only for companies */}
        {clientType === 'company' && (
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Company name</Text>
            <TextInput
              style={inputStyle('company')}
              placeholder="e.g. Acme Pvt. Ltd."
              placeholderTextColor="#b5ad9e"
              value={companyName}
              onChangeText={setCompanyName}
              onFocus={() => setFocused('company')}
              onBlur={() => setFocused(null)}
              autoCapitalize="words"
              returnKeyType="next"
            />
          </View>
        )}

        {/* Contact name */}
        <View style={styles.fieldGroup}>
          <Text style={styles.label}>
            {clientType === 'individual' ? 'Your name' : 'Contact person name'}
          </Text>
          <TextInput
            style={inputStyle('contact')}
            placeholder={clientType === 'individual' ? 'e.g. Arun Kumar' : 'e.g. Priya Sharma'}
            placeholderTextColor="#b5ad9e"
            value={contactName}
            onChangeText={setContactName}
            onFocus={() => setFocused('contact')}
            onBlur={() => setFocused(null)}
            autoCapitalize="words"
            returnKeyType="next"
          />
        </View>

        {/* City + State */}
        <View style={styles.row}>
          <View style={[styles.fieldGroup, styles.flex1]}>
            <Text style={styles.label}>City</Text>
            <TextInput
              style={inputStyle('city')}
              placeholder="Chennai"
              placeholderTextColor="#b5ad9e"
              value={city}
              onChangeText={setCity}
              onFocus={() => setFocused('city')}
              onBlur={() => setFocused(null)}
              autoCapitalize="words"
              returnKeyType="next"
            />
          </View>
          <View style={[styles.fieldGroup, styles.flex1]}>
            <Text style={styles.label}>State</Text>
            <TextInput
              style={inputStyle('state')}
              placeholder="Tamil Nadu"
              placeholderTextColor="#b5ad9e"
              value={state}
              onChangeText={setState}
              onFocus={() => setFocused('state')}
              onBlur={() => setFocused(null)}
              autoCapitalize="words"
              returnKeyType="next"
            />
          </View>
        </View>

        {/* Email — for invoice delivery */}
        <View style={styles.fieldGroup}>
          <Text style={styles.label}>
            Email address{' '}
            <Text style={{ color: '#b5ad9e', fontWeight: '400' }}>(optional)</Text>
          </Text>
          <TextInput
            style={inputStyle('email')}
            placeholder="you@example.com"
            placeholderTextColor="#b5ad9e"
            value={email}
            onChangeText={setEmail}
            onFocus={() => setFocused('email')}
            onBlur={() => setFocused(null)}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="done"
          />
          <Text style={styles.fieldHint}>We’ll send payment invoices to this address.</Text>
        </View>

        {/* Trust note */}
        <View style={styles.trustNote}>
          <View style={styles.trustDot} />
          <Text style={styles.trustText}>
            Your info is private and only used to match you with local workers.
          </Text>
        </View>
      </ScrollView>

      {/* Sticky CTA */}
      <View style={styles.footer}>
        <Pressable
          style={({ pressed }) => [styles.ctaBtn, pressed && styles.ctaBtnPressed]}
          onPress={handleSave}
          disabled={isSaving}
        >
          {isSaving ? (
            <ActivityIndicator size="small" color="#ffffff" />
          ) : (
            <Text style={styles.ctaBtnText}>Get Started →</Text>
          )}
        </Pressable>
        <Text style={styles.footerNote}>30-day session · No passwords</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#fdf9f5',
  },
  blobTopRight: {
    position: 'absolute',
    top: -40,
    right: -40,
    width: width * 0.5,
    height: width * 0.5,
    borderRadius: width * 0.25,
    backgroundColor: '#c96f3c',
    opacity: 0.06,
  },
  scroll: { flex: 1 },
  content: {
    paddingHorizontal: 28,
    paddingTop: 16,
    paddingBottom: 32,
    gap: 24,
  },

  // Header
  header: { gap: 10 },
  stepBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#f4f1e8',
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  stepBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#c96f3c',
    letterSpacing: 0.3,
  },
  heading: {
    fontSize: 36,
    fontWeight: '800',
    color: '#17211a',
    letterSpacing: -0.8,
    lineHeight: 42,
  },
  subheading: {
    fontSize: 15,
    color: '#687267',
    lineHeight: 22,
  },

  // Toggle
  toggle: {
    flexDirection: 'row',
    backgroundColor: '#f4f1e8',
    borderRadius: 12,
    padding: 4,
    gap: 4,
  },
  toggleOption: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  toggleActive: {
    backgroundColor: '#203428',
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#687267',
  },
  toggleTextActive: {
    color: '#ffffff',
  },

  // Fields
  fieldGroup: { gap: 8 },
  flex1: { flex: 1 },
  row: { flexDirection: 'row', gap: 12 },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#17211a',
  },
  input: {
    height: 52,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#ddd6c8',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    fontSize: 15,
    color: '#17211a',
  },
  inputFocused: {
    borderColor: '#203428',
  },

  // Trust note
  trustNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#f4f1e8',
    borderRadius: 12,
    padding: 14,
  },
  trustDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#1a6640',
    marginTop: 5,
  },
  trustText: {
    flex: 1,
    fontSize: 13,
    color: '#687267',
    lineHeight: 19,
  },

  // Footer CTA
  footer: {
    paddingHorizontal: 28,
    paddingBottom: 32,
    paddingTop: 16,
    gap: 10,
    backgroundColor: '#fdf9f5',
    borderTopWidth: 1,
    borderTopColor: '#ede8df',
  },
  ctaBtn: {
    height: 56,
    borderRadius: 16,
    backgroundColor: '#203428',
    alignItems: 'center',
    justifyContent: 'center',
  },
  ctaBtnPressed: {
    opacity: 0.85,
  },
  ctaBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  fieldHint: {
    marginTop: 5,
    fontSize: 12,
    color: '#b5ad9e',
  },
  footerNote: {
    textAlign: 'center',
    color: '#b5ad9e',
    fontSize: 12,
  },
});
