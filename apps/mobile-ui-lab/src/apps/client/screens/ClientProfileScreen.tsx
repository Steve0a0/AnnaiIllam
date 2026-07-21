import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { ProfileStackParamList } from '../navigation/types';
import { pushTokenService } from '../../../shared/services/push-token.service';
import {
  Building2,
  ChevronRight,
  LogOut,
  MapPin,
  Pencil,
  ReceiptText,
  Shield,
  Sliders,
  User,
  X,
} from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { authStorage } from '../../../shared/lib/auth-storage';
import { getApiError } from '../../../shared/lib/get-api-error';
import { clientPhoneService, clientProfileService, type ClientProfile, type ClientProfilePatch } from '../../../shared/services/client-profile.service';
import { useAuthStore } from '../../../shared/store/auth.store';
import { LoadingBlock } from './components';
import { C, clientStyles } from './clientStyles';

const JOB_CATEGORIES = [
  'General Labour', 'Security', 'Housekeeping', 'Packing',
  'Loading / Unloading', 'Machine Operator', 'Technical Trainee',
  'Electrician', 'Welder', 'Forklift Operator', 'Other',
];

const INDUSTRIES = [
  'Manufacturing', 'Logistics & Warehousing', 'Construction',
  'Retail & FMCG', 'Hospitality', 'Healthcare', 'Agriculture',
  'IT & Technology', 'Other',
];

export default function ClientProfileScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<ProfileStackParamList>>();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const [profile, setProfile] = useState<ClientProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);
  const [addPhoneOpen, setAddPhoneOpen] = useState(false);

  const load = useCallback(async () => {
    const data = await clientProfileService.getProfile();
    setProfile(data);
  }, []);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load()
        .catch(() => undefined)
        .finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const logout = async () => {
    Alert.alert('Log out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: async () => { await pushTokenService.deactivate().catch(() => undefined); await authStorage.clear(); clearAuth(); } },
    ]);
  };

  const handleSaved = async () => {
    setEditOpen(false);
    setIsLoading(true);
    await load().finally(() => setIsLoading(false));
  };

  const displayName = profile
    ? (profile.client_type === 'company' ? profile.company_name : profile.contact_name) ?? '—'
    : '—';

  return (
    <View style={{ flex: 1, backgroundColor: '#F5F5F4' }}>
      {/* Hero */}
      <View style={[s.hero, { paddingTop: insets.top + 12 }]}>
        <View style={s.heroRow}>
          <View style={s.heroAvatar}>
            <Text style={s.heroAvatarText}>{displayName.slice(0, 2).toUpperCase()}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.heroEyebrow}>
              {profile?.client_type === 'individual' ? 'Individual account' : 'Company account'}
            </Text>
            <Text style={s.heroName}>{displayName}</Text>
            {(profile?.city || profile?.state) ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 }}>
                <MapPin size={11} color="rgba(255,255,255,0.5)" />
                <Text style={s.heroSub}>{[profile?.city, profile?.state].filter(Boolean).join(', ')}</Text>
              </View>
            ) : null}
          </View>
          {profile ? (
            <Pressable style={s.editBtn} onPress={() => setEditOpen(true)}>
              <Pencil size={14} color="rgba(255,255,255,0.9)" />
              <Text style={s.editBtnText}>Edit</Text>
            </Pressable>
          ) : null}
        </View>
        {profile?.client_type === 'company' && profile.gst_number ? (
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Shield size={11} color="rgba(255,255,255,0.35)" />
            <Text style={s.gstText}>GST · {profile.gst_number}</Text>
            <View style={s.verifiedPill}><Text style={s.verifiedText}>verified</Text></View>
          </View>
        ) : null}
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 36 }}>
        {isLoading ? (
          <View style={{ margin: 16 }}><LoadingBlock label="Loading profile..." /></View>
        ) : !profile ? (
          <View style={{ margin: 16, padding: 24, backgroundColor: C.surface, borderRadius: 14, alignItems: 'center' }}>
            <Text style={{ fontSize: 15, fontWeight: '600', color: C.ink }}>Profile unavailable</Text>
          </View>
        ) : (
          <>
            <SectionLabel icon={<Building2 size={13} color={C.muted} />}
              label={profile.client_type === 'individual' ? 'Personal identity' : 'Company identity'} />
            <InfoCard>
              {profile.client_type === 'company' && profile.company_name
                ? <InfoRow label="Company name" value={profile.company_name} /> : null}
              <InfoRow label="Industry" value={profile.industry ?? '—'} />
              <InfoRow label="City" value={profile.city} />
              <InfoRow label="State" value={profile.state} />
              {profile.address ? <InfoRow label="Address" value={profile.address} /> : null}
              {profile.client_type === 'company'
                ? <InfoRow label="GST number" value={profile.gst_number ?? 'Not provided'} badge="locked" /> : null}
            </InfoCard>

            <SectionLabel icon={<User size={13} color={C.muted} />} label="Primary contact" />
            <InfoCard>
              <InfoRow label="Contact name" value={profile.contact_name} />
              <InfoRow label="Phone" value={profile.phone ?? '—'} badge={profile.phone ? 'login' : undefined} />
              {profile.phone ? (
                <Pressable
                  style={s.supportRow}
                  onPress={() => Linking.openURL('mailto:support@annaiillam.com?subject=Phone%20number%20change%20request')}
                >
                  <Text style={s.supportText}>Need to change? Email support@annaiillam.com →</Text>
                </Pressable>
              ) : (
                <Pressable style={s.supportRow} onPress={() => setAddPhoneOpen(true)}>
                  <Text style={[s.supportText, { color: C.brand, fontWeight: '600' }]}>+ Add phone number</Text>
                </Pressable>
              )}
              <InfoRow label="Email" value={profile.email ?? '—'} />
            </InfoCard>

            <SectionLabel icon={<Sliders size={13} color={C.muted} />} label="Preferences & defaults" />
            <InfoCard>
              <InfoRow label="Default category" value={profile.default_job_category ?? '—'} />
              <PrefRow label="Food provided for workers" value={profile.food_preference} />
              <PrefRow label="Accommodation provided" value={profile.accommodation_preference} />
              {profile.standing_notes ? (
                <View style={s.notesBox}>
                  <Text style={s.notesLabel}>Standing instructions</Text>
                  <Text style={s.notesBody}>{profile.standing_notes}</Text>
                </View>
              ) : null}
            </InfoCard>

            <SectionLabel icon={<ReceiptText size={13} color={C.muted} />} label="Billing" />
            <InfoCard>
              <Pressable style={s.actionRow} onPress={() => navigation.navigate('BillingOverview')}>
                <ReceiptText size={15} color={C.body} />
                <Text style={s.actionLabel}>My Invoices &amp; Payments</Text>
                <ChevronRight size={15} color={C.muted} />
              </Pressable>
            </InfoCard>

            <SectionLabel icon={<Shield size={13} color={C.muted} />} label="Account" />
            <InfoCard>
              <Pressable style={s.actionRow} onPress={logout}>
                <LogOut size={15} color={C.dangerText} />
                <Text style={[s.actionLabel, { color: C.dangerText }]}>Log out</Text>
                <ChevronRight size={15} color={C.dangerText} />
              </Pressable>
              <View style={s.hairline} />
              <Pressable style={s.actionRow} onPress={() => navigation.navigate('PrivacySettings')}>
                <Shield size={15} color={C.body} />
                <Text style={[s.actionLabel, { color: C.body }]}>Privacy and data</Text>
                <ChevronRight size={15} color={C.muted} />
              </Pressable>
            </InfoCard>
          </>
        )}
      </ScrollView>

      {profile ? (
        <EditSheet profile={profile} visible={editOpen} onClose={() => setEditOpen(false)} onSaved={handleSaved} />
      ) : null}
      {profile && !profile.phone ? (
        <AddPhoneSheet
          visible={addPhoneOpen}
          onClose={() => setAddPhoneOpen(false)}
          onSaved={() => {
            setAddPhoneOpen(false);
            setIsLoading(true);
            load().finally(() => setIsLoading(false));
          }}
        />
      ) : null}
    </View>
  );
}

/* Sub-components */
function SectionLabel({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 16, paddingTop: 20, paddingBottom: 7 }}>
      {icon}
      <Text style={{ fontSize: 10, fontWeight: '600', color: C.muted, letterSpacing: 1, textTransform: 'uppercase' }}>{label}</Text>
    </View>
  );
}

function InfoCard({ children }: { children: React.ReactNode }) {
  return <View style={s.infoCard}>{children}</View>;
}

function InfoRow({ label, value, badge, note }: {
  label: string; value: string; badge?: 'locked' | 'login'; note?: string;
}) {
  return (
    <View style={s.infoRow}>
      <Text style={s.infoLabel}>{label}</Text>
      <View style={{ flex: 1, alignItems: 'flex-end', gap: 3 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <Text style={s.infoValue}>{value}</Text>
          {badge ? (
            <View style={[s.pill, badge === 'locked' ? s.pillBlue : s.pillAmber]}>
              <Text style={[s.pillText, badge === 'locked' ? { color: '#1D4ED8' } : { color: '#B45309' }]}>{badge}</Text>
            </View>
          ) : null}
        </View>
        {note ? <Text style={s.infoNote}>{note}</Text> : null}
      </View>
    </View>
  );
}

function PrefRow({ label, value }: { label: string; value: boolean }) {
  return (
    <View style={[s.infoRow, { alignItems: 'center' }]}>
      <Text style={s.infoLabel}>{label}</Text>
      <View style={[s.prefPill, value ? s.prefOn : s.prefOff]}>
        <Text style={[s.prefText, value ? { color: C.successText } : { color: C.muted }]}>{value ? 'Yes' : 'No'}</Text>
      </View>
    </View>
  );
}

/* Edit Sheet */
type EditForm = {
  company_name: string; contact_name: string; city: string; state: string;
  address: string; industry: string; email: string; default_job_category: string;
  food_preference: boolean; accommodation_preference: boolean; standing_notes: string;
};

function EditSheet({ profile, visible, onClose, onSaved }: {
  profile: ClientProfile; visible: boolean; onClose: () => void; onSaved: () => void;
}) {
  const [form, setForm] = useState<EditForm>({
    company_name: profile.company_name ?? '',
    contact_name: profile.contact_name,
    city: profile.city, state: profile.state,
    address: profile.address ?? '',
    industry: profile.industry ?? '',
    email: profile.email ?? '',
    default_job_category: profile.default_job_category ?? '',
    food_preference: profile.food_preference,
    accommodation_preference: profile.accommodation_preference,
    standing_notes: profile.standing_notes ?? '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [showCatPicker, setShowCatPicker] = useState(false);
  const [showIndPicker, setShowIndPicker] = useState(false);

  const set = <K extends keyof EditForm>(k: K, v: EditForm[K]) => setForm((p) => ({ ...p, [k]: v }));

  const save = async () => {
    if (profile.client_type === 'company' && !form.company_name.trim()) {
      Alert.alert('Required', 'Company name is required.'); return;
    }
    if (!form.contact_name.trim() || !form.city.trim()) {
      Alert.alert('Required', 'Contact name and city are required.'); return;
    }
    setIsSaving(true);
    try {
      const patch: ClientProfilePatch = {
        company_name: form.company_name.trim() || null,
        contact_name: form.contact_name.trim(),
        city: form.city.trim(), state: form.state.trim(),
        address: form.address.trim() || null,
        industry: form.industry.trim() || null,
        email: form.email.trim() || null,
        default_job_category: form.default_job_category || null,
        food_preference: form.food_preference,
        accommodation_preference: form.accommodation_preference,
        standing_notes: form.standing_notes.trim() || null,
      };
      await clientProfileService.patchProfile(patch);
      onSaved();
    } catch { Alert.alert('Could not save', 'Please try again.'); }
    finally { setIsSaving(false); }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={es.root}>
        <View style={es.handle} />
        <View style={es.header}>
          <Text style={es.headerTitle}>Edit profile</Text>
          <Pressable onPress={onClose} style={es.closeBtn}><X size={18} color={C.body} /></Pressable>
        </View>
        <ScrollView style={{ flex: 1 }} contentContainerStyle={es.body} keyboardShouldPersistTaps="handled">
          <Text style={es.groupLabel}>{profile.client_type === 'individual' ? 'Personal identity' : 'Company identity'}</Text>
          {profile.client_type === 'company'
            ? <EField label="Company name *" value={form.company_name} onChange={(v) => set('company_name', v)} /> : null}
          <Text style={clientStyles.fieldLabel}>Industry / Sector</Text>
          <Pressable style={es.pickerRow} onPress={() => setShowIndPicker(true)}>
            <Text style={form.industry ? es.pickerVal : es.pickerMuted}>{form.industry || 'Select industry'}</Text>
            <ChevronRight size={16} color={C.muted} />
          </Pressable>
          {showIndPicker
            ? <Picker options={INDUSTRIES} selected={form.industry}
                onSelect={(v) => { set('industry', v); setShowIndPicker(false); }}
                onClose={() => setShowIndPicker(false)} /> : null}
          <EField label="City *" value={form.city} onChange={(v) => set('city', v)} />
          <EField label="State" value={form.state} onChange={(v) => set('state', v)} />
          <EField label="Address" value={form.address} onChange={(v) => set('address', v)} multiline />

          <Text style={es.groupLabel}>Primary contact</Text>
          <EField label="Contact name *" value={form.contact_name} onChange={(v) => set('contact_name', v)} />
          <EField label="Email" value={form.email} onChange={(v) => set('email', v)} keyboardType="email-address" />

          <Text style={es.groupLabel}>Preferences & defaults</Text>
          <Text style={clientStyles.fieldLabel}>Default job category</Text>
          <Pressable style={es.pickerRow} onPress={() => setShowCatPicker(true)}>
            <Text style={form.default_job_category ? es.pickerVal : es.pickerMuted}>{form.default_job_category || 'Select category'}</Text>
            <ChevronRight size={16} color={C.muted} />
          </Pressable>
          {showCatPicker
            ? <Picker options={JOB_CATEGORIES} selected={form.default_job_category}
                onSelect={(v) => { set('default_job_category', v); setShowCatPicker(false); }}
                onClose={() => setShowCatPicker(false)} /> : null}
          <View style={es.switchRow}>
            <Text style={es.switchLabel}>Food provided for workers</Text>
            <Switch value={form.food_preference} onValueChange={(v) => set('food_preference', v)}
              trackColor={{ false: C.border, true: C.brand }} thumbColor="#FFF" />
          </View>
          <View style={es.switchRow}>
            <Text style={es.switchLabel}>Accommodation provided</Text>
            <Switch value={form.accommodation_preference} onValueChange={(v) => set('accommodation_preference', v)}
              trackColor={{ false: C.border, true: C.brand }} thumbColor="#FFF" />
          </View>
          <EField label="Standing instructions" value={form.standing_notes}
            onChange={(v) => set('standing_notes', v)} multiline
            placeholder="e.g. Workers must wear safety shoes. Report to gate 3." />
        </ScrollView>
        <View style={es.footer}>
          <Pressable style={[es.saveBtn, isSaving && { opacity: 0.6 }]} onPress={save} disabled={isSaving}>
            {isSaving ? <ActivityIndicator color="#FFF" size="small" /> : <Text style={es.saveBtnText}>Save changes</Text>}
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

/* Add Phone Sheet */
const OTP_LENGTH = 6;

export function AddPhoneSheet({ visible, onClose, onSaved, required = false, title, subtitle }: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
  required?: boolean;
  title?: string;
  subtitle?: string;
}) {
  const { user, updateUser } = useAuthStore();
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [devOtp, setDevOtp] = useState<string | undefined>(undefined);
  const [isPending, setIsPending] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const inputRef = useRef<TextInput>(null);

  const digits = Array.from({ length: OTP_LENGTH }, (_, i) => code[i] ?? '');
  const isPhoneValid = /^\d{10,15}$/.test(phone.trim());
  const isOtpValid = code.length === OTP_LENGTH;
  const maskedPhone = phone.length > 4
    ? `${phone.slice(0, 4)} ${phone.slice(4, 6)} ****${phone.slice(-3)}`
    : phone;

  useEffect(() => {
    if (visible) {
      setStep('phone');
      setPhone('');
      setCode('');
      setDevOtp(undefined);
      setIsPending(false);
      setCooldown(0);
    }
  }, [visible]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((s) => (s <= 1 ? 0 : s - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  useEffect(() => {
    if (step === 'otp') {
      const t = setTimeout(() => inputRef.current?.focus(), 300);
      return () => clearTimeout(t);
    }
  }, [step]);

  const handleSendOtp = async () => {
    if (!isPhoneValid) return;
    setIsPending(true);
    try {
      const result = await clientPhoneService.requestOtp(phone.trim());
      setDevOtp(result.otp);
      setStep('otp');
      setCooldown(30);
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Could not send OTP. Please try again.'));
    } finally {
      setIsPending(false);
    }
  };

  const handleVerify = async () => {
    if (!isOtpValid) return;
    Keyboard.dismiss();
    setIsPending(true);
    try {
      const result = await clientPhoneService.verify(phone.trim(), code);
      if (user) {
        const updatedUser = { ...user, phone: result.phone };
        await authStorage.setUser(updatedUser);
        updateUser({ phone: result.phone });
      }
      onSaved();
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Invalid OTP. Please try again.'));
    } finally {
      setIsPending(false);
    }
  };

  const handleResend = async () => {
    if (isResending || cooldown > 0) return;
    setIsResending(true);
    try {
      const result = await clientPhoneService.requestOtp(phone.trim());
      setDevOtp(result.otp);
      setCode('');
      setCooldown(30);
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Could not resend OTP.'));
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={required ? undefined : onClose}
    >
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={ph.root}>
          <View style={ph.handle} />
          <View style={ph.header}>
            <Text style={ph.headerTitle}>
              {step === 'phone' ? title ?? 'Add phone number' : 'Verify your number'}
            </Text>
            {!required ? (
              <Pressable onPress={onClose} style={ph.closeBtn}>
                <X size={18} color={C.body} />
              </Pressable>
            ) : null}
          </View>

          <View style={ph.body}>
            {step === 'phone' ? (
              <>
                <Text style={ph.subtitle}>
                  {subtitle ?? 'Enter your mobile number. We will send a 6-digit code to verify it.'}
                </Text>
                <Text style={clientStyles.fieldLabel}>Phone number</Text>
                <View style={ph.inputShell}>
                  <Text style={ph.prefix}>+91</Text>
                  <View style={ph.divider} />
                  <TextInput
                    style={ph.input}
                    placeholder="Your phone number"
                    placeholderTextColor={C.muted}
                    keyboardType="phone-pad"
                    value={phone}
                    onChangeText={(v) => setPhone(v.replace(/\D/g, ''))}
                    returnKeyType="done"
                    onSubmitEditing={handleSendOtp}
                    autoFocus
                  />
                </View>
              </>
            ) : (
              <>
                <Text style={ph.subtitle}>Code sent to +91 {maskedPhone}</Text>
                {!!devOtp && (
                  <Pressable
                    style={ph.devBanner}
                    onPress={() => setCode(devOtp.slice(0, OTP_LENGTH))}
                  >
                    <Text style={ph.devBannerText}>Dev OTP: {devOtp}</Text>
                  </Pressable>
                )}
                <Pressable style={ph.boxesRow} onPress={() => inputRef.current?.focus()}>
                  {digits.map((digit, index) => {
                    const filled = digit !== '';
                    return (
                      <View key={index} style={[ph.box, filled && ph.boxFilled]}>
                        <Text style={[ph.dot, filled && ph.dotFilled]}>{filled ? '*' : ''}</Text>
                      </View>
                    );
                  })}
                </Pressable>
                <TextInput
                  ref={inputRef}
                  style={{ position: 'absolute', width: 0, height: 0, opacity: 0 }}
                  value={code}
                  onChangeText={(v) => setCode(v.replace(/\D/g, '').slice(0, OTP_LENGTH))}
                  keyboardType="number-pad"
                  maxLength={OTP_LENGTH}
                  caretHidden
                />
                <View style={ph.resendRow}>
                  <Text style={ph.resendText}>Did not get it? </Text>
                  <Pressable onPress={handleResend} disabled={isResending || cooldown > 0}>
                    <Text style={[ph.resendLink, (isResending || cooldown > 0) && ph.resendLinkDisabled]}>
                      {isResending ? 'Sending...' : cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
                    </Text>
                  </Pressable>
                </View>
              </>
            )}
          </View>

          <View style={ph.footer}>
            {step === 'phone' ? (
              <Pressable
                style={[ph.btn, (!isPhoneValid || isPending) && { opacity: 0.5 }]}
                onPress={handleSendOtp}
                disabled={!isPhoneValid || isPending}
              >
                {isPending
                  ? <ActivityIndicator color="#FFF" size="small" />
                  : <Text style={ph.btnText}>Send code</Text>}
              </Pressable>
            ) : (
              <Pressable
                style={[ph.btn, (!isOtpValid || isPending) && { opacity: 0.5 }]}
                onPress={handleVerify}
                disabled={!isOtpValid || isPending}
              >
                {isPending
                  ? <ActivityIndicator color="#FFF" size="small" />
                  : <Text style={ph.btnText}>Verify & save</Text>}
              </Pressable>
            )}
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function EField({ label, value, onChange, multiline = false, placeholder, keyboardType }: {
  label: string; value: string; onChange: (v: string) => void;
  multiline?: boolean; placeholder?: string; keyboardType?: 'default' | 'email-address' | 'numeric';
}) {
  return (
    <View style={{ marginBottom: 14 }}>
      <Text style={clientStyles.fieldLabel}>{label}</Text>
      <TextInput style={[clientStyles.input, multiline && clientStyles.textArea]}
        value={value} onChangeText={onChange}
        placeholder={placeholder ?? label.replace(' *', '')}
        placeholderTextColor={C.muted} multiline={multiline}
        keyboardType={keyboardType ?? 'default'} autoCapitalize="none" />
    </View>
  );
}

function Picker({ options, selected, onSelect, onClose }: {
  options: string[]; selected: string; onSelect: (v: string) => void; onClose: () => void;
}) {
  return (
    <View style={pk.root}>
      <View style={pk.header}>
        <Text style={pk.title}>Select option</Text>
        <Pressable onPress={onClose}><X size={16} color={C.body} /></Pressable>
      </View>
      {options.map((opt) => (
        <Pressable key={opt} style={[pk.item, opt === selected && pk.itemActive]} onPress={() => onSelect(opt)}>
          <Text style={[pk.text, opt === selected && pk.textActive]}>{opt}</Text>
        </Pressable>
      ))}
    </View>
  );
}

/* Styles */
const s = StyleSheet.create({
  hero: { backgroundColor: '#0D2E1E', paddingHorizontal: 20, paddingBottom: 20 },
  heroRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 14, marginBottom: 10 },
  heroAvatar: {
    width: 52, height: 52, borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center', justifyContent: 'center',
  },
  heroAvatarText: { fontSize: 20, fontWeight: '600', color: '#FFF' },
  heroEyebrow: { fontSize: 10, fontWeight: '600', letterSpacing: 0.8, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: 3 },
  heroName: { fontSize: 20, fontWeight: '600', color: '#FFF', lineHeight: 26 },
  heroSub: { fontSize: 12, color: 'rgba(255,255,255,0.5)' },
  gstText: { fontSize: 12, color: 'rgba(255,255,255,0.4)', flex: 1 },
  verifiedPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999, backgroundColor: 'rgba(37,162,99,0.25)' },
  verifiedText: { fontSize: 10, fontWeight: '600', color: '#a7f3d0', letterSpacing: 0.5 },
  editBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    paddingHorizontal: 11, paddingVertical: 7, borderRadius: 8,
    borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.2)',
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  editBtnText: { fontSize: 13, fontWeight: '500', color: 'rgba(255,255,255,0.9)' },
  infoCard: {
    marginHorizontal: 16, backgroundColor: C.surface,
    borderRadius: 14, borderWidth: 0.5, borderColor: C.border, overflow: 'hidden',
  },
  infoRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    paddingHorizontal: 16, paddingVertical: 13,
    borderBottomWidth: 0.5, borderBottomColor: '#F0EFED', gap: 8,
  },
  infoLabel: { fontSize: 13, color: C.muted, width: 130, lineHeight: 20 },
  infoValue: { fontSize: 13, fontWeight: '500', color: C.ink, lineHeight: 20, textAlign: 'right' },
  infoNote: { fontSize: 11, color: C.muted, fontStyle: 'italic', textAlign: 'right', lineHeight: 16 },
  pill: { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  pillBlue: { backgroundColor: '#DBEAFE' },
  pillAmber: { backgroundColor: '#FEF3C7' },
  pillText: { fontSize: 10, fontWeight: '600', letterSpacing: 0.4 },
  prefPill: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 999 },
  prefOn: { backgroundColor: C.successBg },
  prefOff: { backgroundColor: C.border },
  prefText: { fontSize: 12, fontWeight: '600' },
  notesBox: { margin: 16, padding: 12, borderRadius: 10, backgroundColor: '#FAFAF9', borderWidth: 0.5, borderColor: C.border },
  notesLabel: { fontSize: 10, fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  notesBody: { fontSize: 13, color: C.body, lineHeight: 20 },
  actionRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, paddingVertical: 14 },
  actionLabel: { flex: 1, fontSize: 14, fontWeight: '500' },
  hairline: { height: 0.5, backgroundColor: C.border },
  supportRow: { paddingHorizontal: 16, paddingVertical: 10 },
  supportText: { fontSize: 12, color: C.brand, fontWeight: '500' },
});

const es = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F5F5F4' },
  handle: { width: 36, height: 4, borderRadius: 2, backgroundColor: C.border, alignSelf: 'center', marginTop: 12, marginBottom: 4 },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: C.border, backgroundColor: C.surface },
  headerTitle: { flex: 1, fontSize: 17, fontWeight: '600', color: C.ink },
  closeBtn: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F5F5F4', borderWidth: 0.5, borderColor: C.border },
  body: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 24 },
  groupLabel: { fontSize: 10, fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: 1, marginTop: 16, marginBottom: 14 },
  pickerRow: { flexDirection: 'row', alignItems: 'center', borderWidth: 0.5, borderColor: C.border, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 14, backgroundColor: C.surface, marginBottom: 14 },
  pickerVal: { flex: 1, fontSize: 14, color: C.ink },
  pickerMuted: { flex: 1, fontSize: 14, color: C.muted },
  switchRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: C.border, marginBottom: 14 },
  switchLabel: { flex: 1, fontSize: 14, fontWeight: '500', color: C.body },
  footer: { padding: 16, borderTopWidth: 0.5, borderTopColor: C.border, backgroundColor: C.surface },
  saveBtn: { minHeight: 52, borderRadius: 12, backgroundColor: C.brand, alignItems: 'center', justifyContent: 'center' },
  saveBtnText: { color: '#FFF', fontSize: 15, fontWeight: '600' },
});

const pk = StyleSheet.create({
  root: { borderWidth: 0.5, borderColor: C.border, borderRadius: 10, backgroundColor: C.surface, marginBottom: 14, overflow: 'hidden' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 12, borderBottomWidth: 0.5, borderBottomColor: C.border, backgroundColor: '#FAFAF9' },
  title: { flex: 1, fontSize: 11, fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8 },
  item: { paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: C.border },
  itemActive: { backgroundColor: C.brandSoft },
  text: { fontSize: 14, color: C.body },
  textActive: { color: C.brand, fontWeight: '600' },
});

const ph = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F5F5F4' },
  handle: { width: 36, height: 4, borderRadius: 2, backgroundColor: C.border, alignSelf: 'center', marginTop: 12, marginBottom: 4 },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: C.border, backgroundColor: C.surface },
  headerTitle: { flex: 1, fontSize: 17, fontWeight: '600', color: C.ink },
  closeBtn: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F5F5F4', borderWidth: 0.5, borderColor: C.border },
  body: { flex: 1, paddingHorizontal: 20, paddingTop: 24 },
  subtitle: { fontSize: 14, color: C.muted, lineHeight: 20, marginBottom: 20 },
  inputShell: { flexDirection: 'row', alignItems: 'center', height: 52, borderRadius: 12, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, paddingHorizontal: 14, marginTop: 6 },
  prefix: { fontSize: 15, fontWeight: '600', color: C.ink, paddingRight: 10 },
  divider: { width: 1, height: 20, backgroundColor: C.border, marginRight: 12 },
  input: { flex: 1, fontSize: 15, color: C.ink },
  devBanner: { borderWidth: 1, borderColor: '#c96f3c', backgroundColor: '#f0dfd3', borderRadius: 10, padding: 10, marginBottom: 16 },
  devBannerText: { color: C.ink, fontSize: 12, fontWeight: '700', textAlign: 'center' },
  boxesRow: { flexDirection: 'row', gap: 10 },
  box: { flex: 1, maxWidth: 54, height: 52, borderRadius: 10, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surface, alignItems: 'center', justifyContent: 'center' },
  boxFilled: { borderColor: C.brand, backgroundColor: '#FAFAF9' },
  dot: { color: C.muted, fontSize: 22, fontWeight: '900' },
  dotFilled: { color: C.brand },
  resendRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 16 },
  resendText: { color: C.muted, fontSize: 12 },
  resendLink: { color: C.brand, fontSize: 12, fontWeight: '700', textDecorationLine: 'underline' },
  resendLinkDisabled: { color: C.muted, textDecorationLine: 'none', fontWeight: '500' },
  footer: { padding: 16, borderTopWidth: 0.5, borderTopColor: C.border, backgroundColor: C.surface },
  btn: { minHeight: 52, borderRadius: 12, backgroundColor: C.brand, alignItems: 'center', justifyContent: 'center' },
  btnText: { color: '#FFF', fontSize: 15, fontWeight: '600' },
});
