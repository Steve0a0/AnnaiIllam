import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, Switch } from 'react-native';
import {
  Briefcase,
  CalendarDays,
  ChevronRight,
  CreditCard,
  MapPin,
  Phone,
  User,
} from 'lucide-react-native';
import {
  Button,
  Card,
  ScrollView,
  Text,
  View,
  XStack,
  YStack,
} from 'tamagui';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { http } from '../../../shared/lib/http';
import { workerProfileService } from '../../../shared/services/worker-profile.service';
import { useAuthStore } from '../../../shared/store/auth.store';
import { workerAssignmentsService } from '../../../shared/services/worker-assignments.service';
import { workerAttendanceService } from '../../../shared/services/worker-attendance.service';
import type { ProfileStackParamList } from '../navigation/types';

type Navigation = NativeStackNavigationProp<ProfileStackParamList>;

const C = {
  page: '#F5F5F4',
  card: '#FFFFFF',
  brand900: '#0D2E1E',
  brand700: '#165233',
  brand600: '#1A6640',
  brand400: '#25A263',
  brand100: '#D4F0E3',
  neutral900: '#1C1917',
  neutral700: '#44403C',
  neutral500: '#78716C',
  neutral300: '#D6D3D1',
  neutral200: '#E7E5E4',
  success100: '#DCFCE7',
  success700: '#15803D',
  warning100: '#FEF3C7',
  warning700: '#B45309',
  danger100: '#FEE2E2',
  danger700: '#B91C1C',
};

type Envelope<T> = { success: boolean; message: string; data: T };

type WorkerFullProfile = {
  id: number;
  full_name: string;
  category: string | null;
  subcategory: string | null;
  city: string;
  state: string;
  address: string | null;
  date_of_birth: string | null;
  skills: string[] | null;
  experience_notes: string | null;
  available_days: string[] | null;
  available_shifts: string[] | null;
  is_available: boolean;
  verification_status: string;
  documents: {
    id: number;
    document_type: string;
    file_url: string | null;
  }[];
};

const verificationMeta: Record<string, { label: string; bg: string; color: string }> = {
  pending: { label: 'Under Review', bg: C.warning100, color: C.warning700 },
  approved: { label: 'Verified', bg: C.success100, color: C.success700 },
  rejected: { label: 'Not Approved', bg: C.danger100, color: C.danger700 },
};

export default function ProfileScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);

  const [profile, setProfile] = useState<WorkerFullProfile | null>(null);
  const [jobsDone, setJobsDone] = useState<number>(0);
  const [attendancePct, setAttendancePct] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTogglingAvailability, setIsTogglingAvailability] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [profileRes, assignments, attendance] = await Promise.all([
        http.get<Envelope<WorkerFullProfile>>('/worker/profile'),
        workerAssignmentsService.list().catch(() => []),
        workerAttendanceService.list().catch(() => []),
      ]);
      setProfile(profileRes.data.data);
      setJobsDone(assignments.filter((a) => a.status === 'completed').length);
      const total = attendance.length;
      const present = attendance.filter((r) => r.status === 'present' || r.status === 'approved').length;
      setAttendancePct(total > 0 ? Math.round((present / total) * 100) : null);
    } catch {
      setError('Could not load profile. Pull down to retry.');
    }
  }, []);

  const toggleAvailability = async (next: boolean) => {
    if (!profile) return;
    setIsTogglingAvailability(true);
    try {
      const result = await workerProfileService.patch({ is_available: next });
      setProfile((prev) => prev ? { ...prev, is_available: result.is_available } : prev);
    } catch {
      Alert.alert('Could not update availability', 'Please try again.');
    } finally {
      setIsTogglingAvailability(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setIsLoading(true);
      load().finally(() => active && setIsLoading(false));
      return () => { active = false; };
    }, [load]),
  );

  const initials = profile?.full_name
    ? profile.full_name
        .split(' ')
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase()
    : '?';

  const verif = profile
    ? (verificationMeta[profile.verification_status] ?? {
        label: profile.verification_status,
        bg: C.neutral200,
        color: C.neutral500,
      })
    : null;

  return (
    <View flex={1} backgroundColor={C.page} paddingTop={insets.top}>
      {/* Header */}
      <XStack height={56} paddingHorizontal={20} alignItems="center">
        <Text fontSize={17} fontWeight="600" color={C.neutral900} flex={1}>
          My Profile
        </Text>
      </XStack>

      {isLoading ? (
        <YStack flex={1} alignItems="center" justifyContent="center" gap={12}>
          <ActivityIndicator size="large" color={C.brand600} />
          <Text fontSize={14} color={C.neutral500}>Loading profile...</Text>
        </YStack>
      ) : error || !profile ? (
        <YStack flex={1} alignItems="center" justifyContent="center" paddingHorizontal={32} gap={12}>
          <User size={40} color={C.neutral300} />
          <Text fontSize={16} fontWeight="500" color={C.neutral900} textAlign="center">
            Could not load profile
          </Text>
          <Text fontSize={13} color={C.neutral500} textAlign="center">
            {error ?? 'No profile data found.'}
          </Text>
          <Button
            height={44}
            borderRadius={12}
            backgroundColor={C.brand600}
            pressStyle={{ backgroundColor: C.brand900, scale: 0.98 }}
            onPress={() => { setIsLoading(true); load().finally(() => setIsLoading(false)); }}
          >
            <Text color="#FFFFFF" fontSize={14} fontWeight="500">Try Again</Text>
          </Button>
        </YStack>
      ) : (
        <ScrollView showsVerticalScrollIndicator={false}>
          <YStack paddingBottom={insets.bottom + 32}>

            {/* Avatar hero */}
            <YStack
              marginHorizontal={16}
              marginTop={8}
              borderRadius={24}
              padding={24}
              backgroundColor={C.brand900}
              alignItems="center"
              gap={12}
            >
              {/* Avatar circle */}
              <View
                width={72}
                height={72}
                borderRadius={36}
                backgroundColor="rgba(255,255,255,0.12)"
                borderWidth={2}
                borderColor="rgba(255,255,255,0.2)"
                alignItems="center"
                justifyContent="center"
              >
                <Text fontSize={24} fontWeight="600" color="#FFFFFF">
                  {initials}
                </Text>
              </View>

              <YStack alignItems="center" gap={4}>
                <Text fontSize={20} fontWeight="500" color="#FFFFFF">
                  {profile.full_name}
                </Text>
                {profile.city ? (
                  <XStack alignItems="center" gap={5}>
                    <MapPin size={13} color="rgba(255,255,255,0.5)" />
                    <Text fontSize={13} color="rgba(255,255,255,0.55)">
                      {profile.city}, {profile.state}
                    </Text>
                  </XStack>
                ) : null}
              </YStack>

              {/* Status + availability row */}
              <XStack gap={8} flexWrap="wrap" justifyContent="center">
                {verif ? (
                  <XStack
                    height={26}
                    borderRadius={999}
                    paddingHorizontal={10}
                    alignItems="center"
                    gap={5}
                    backgroundColor="rgba(255,255,255,0.10)"
                    borderWidth={1}
                    borderColor="rgba(255,255,255,0.15)"
                  >
                    <View width={6} height={6} borderRadius={999} backgroundColor={verif.color} />
                    <Text fontSize={12} fontWeight="500" color="rgba(255,255,255,0.80)">
                      {verif.label}
                    </Text>
                  </XStack>
                ) : null}

              </XStack>

              {/* Stats row */}
              <View height={1} backgroundColor="rgba(255,255,255,0.12)" width="100%" />
              <XStack width="100%" justifyContent="space-around" paddingVertical={4}>
                <YStack alignItems="center" gap={2}>
                  <Text fontSize={22} fontWeight="600" color="#FFFFFF" fontFamily="$mono">
                    {jobsDone}
                  </Text>
                  <Text fontSize={11} fontWeight="500" color="rgba(255,255,255,0.5)">
                    JOBS DONE
                  </Text>
                </YStack>
                <View width={1} height={36} backgroundColor="rgba(255,255,255,0.12)" alignSelf="center" />
                <YStack alignItems="center" gap={2}>
                  <Text fontSize={22} fontWeight="600" color="#FFFFFF" fontFamily="$mono">
                    {attendancePct !== null ? `${attendancePct}%` : '—'}
                  </Text>
                  <Text fontSize={11} fontWeight="500" color="rgba(255,255,255,0.5)">
                    ATTENDANCE
                  </Text>
                </YStack>
                <View width={1} height={36} backgroundColor="rgba(255,255,255,0.12)" alignSelf="center" />
                <YStack alignItems="center" gap={2}>
                  <Text fontSize={22} fontWeight="600" color="#FFFFFF" fontFamily="$mono">
                    —
                  </Text>
                  <Text fontSize={11} fontWeight="500" color="rgba(255,255,255,0.5)">
                    RATING
                  </Text>
                </YStack>
              </XStack>
            </YStack>

            {/* Personal info */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <SectionLabel icon={<User size={14} color={C.neutral500} />} label="PERSONAL INFO" />
              <InfoCard>
                {user?.phone ? (
                  <>
                    <InfoRow
                      label="Phone"
                      value={user.phone}
                      icon={<Phone size={14} color={C.neutral500} />}
                      mono
                    />
                    <Divider />
                  </>
                ) : null}
                <InfoRow
                  label="City"
                  value={`${profile.city}, ${profile.state}`}
                  icon={<MapPin size={14} color={C.neutral500} />}
                />
                {profile.address ? (
                  <>
                    <Divider />
                    <InfoRow label="Address" value={profile.address} />
                  </>
                ) : null}
                {profile.date_of_birth ? (
                  <>
                    <Divider />
                    <InfoRow
                      label="Date of birth"
                      value={formatDate(profile.date_of_birth)}
                      icon={<CalendarDays size={14} color={C.neutral500} />}
                      mono
                    />
                  </>
                ) : null}
              </InfoCard>
            </YStack>

            {/* Skills & experience */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <SectionLabel icon={<Briefcase size={14} color={C.neutral500} />} label="SKILLS & EXPERIENCE" />
              <Card
                bordered
                borderRadius={14}
                borderColor={C.neutral200}
                backgroundColor={C.card}
                padding={16}
              >
                {Array.isArray(profile.skills) && profile.skills.length > 0 ? (
                  <YStack gap={10}>
                    <Text fontSize={12} color={C.neutral500}>Skills</Text>
                    <XStack gap={8} flexWrap="wrap">
                      {profile.skills.map((skill) => (
                        <XStack
                          key={skill}
                          height={28}
                          borderRadius={999}
                          paddingHorizontal={12}
                          alignItems="center"
                          backgroundColor={C.brand100}
                        >
                          <Text fontSize={12} fontWeight="500" color={C.brand700}>
                            {skill}
                          </Text>
                        </XStack>
                      ))}
                    </XStack>
                  </YStack>
                ) : (
                  <Text fontSize={13} color={C.neutral500}>No skills listed</Text>
                )}

                {profile.experience_notes ? (
                  <>
                    <View height={1} backgroundColor={C.neutral200} marginTop={12} marginBottom={12} />
                    <Text fontSize={12} color={C.neutral500} marginBottom={4}>Experience</Text>
                    <Text fontSize={13} color={C.neutral700} lineHeight={20}>
                      {profile.experience_notes}
                    </Text>
                  </>
                ) : null}
              </Card>
            </YStack>

            {/* Availability toggle — interactive */}
            <YStack marginHorizontal={16} marginTop={20} gap={12}>
              <SectionLabel icon={<CalendarDays size={14} color={C.neutral500} />} label="AVAILABILITY" />
              <YStack
                backgroundColor={C.card}
                borderRadius={14}
                borderWidth={1}
                borderColor={C.neutral200}
                overflow="hidden"
              >
                {/* On/off master toggle */}
                <XStack
                  paddingHorizontal={16}
                  paddingVertical={14}
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <YStack flex={1} gap={2}>
                    <Text fontSize={14} fontWeight="500" color={C.neutral900}>
                      Open to assignments
                    </Text>
                    <Text fontSize={12} color={C.neutral500}>
                      {profile.is_available
                        ? 'Admin can assign you new jobs'
                        : 'You will not appear in job matching'}
                    </Text>
                  </YStack>
                  <Switch
                    value={profile.is_available}
                    onValueChange={toggleAvailability}
                    disabled={isTogglingAvailability}
                    trackColor={{ false: C.neutral300, true: C.brand400 }}
                    thumbColor="#FFFFFF"
                  />
                </XStack>
                <Divider />
                <InfoRow
                  label="Working days"
                  value={profile.available_days?.join(', ') || 'Not set'}
                  icon={<CalendarDays size={14} color={C.neutral500} />}
                />
                <Divider />
                <InfoRow
                  label="Preferred shifts"
                  value={profile.available_shifts?.join(', ') || 'Not set'}
                />
              </YStack>
            </YStack>

            {/* Documents */}
            {profile.documents && profile.documents.length > 0 ? (
              <YStack marginHorizontal={16} marginTop={20} gap={12}>
                <SectionLabel icon={<CreditCard size={14} color={C.neutral500} />} label="DOCUMENTS" />
                <Card
                  bordered
                  borderRadius={14}
                  borderColor={C.neutral200}
                  backgroundColor={C.card}
                  paddingVertical={4}
                >
                  {profile.documents.map((doc, index) => (
                    <React.Fragment key={doc.id}>
                      {index > 0 && <Divider />}
                      <XStack
                        paddingHorizontal={16}
                        paddingVertical={14}
                        alignItems="center"
                        justifyContent="space-between"
                      >
                        <YStack flex={1}>
                          <Text fontSize={13} fontWeight="500" color={C.neutral900}>
                            {formatDocType(doc.document_type)}
                          </Text>
                          <Text fontSize={12} color={C.neutral500} marginTop={2}>
                            {doc.file_url ? 'Uploaded' : 'Not uploaded'}
                          </Text>
                        </YStack>
                        <XStack
                          height={24}
                          borderRadius={999}
                          paddingHorizontal={10}
                          alignItems="center"
                          backgroundColor={doc.file_url ? C.success100 : C.neutral200}
                        >
                          <Text
                            fontSize={12}
                            fontWeight="500"
                            color={doc.file_url ? C.success700 : C.neutral500}
                          >
                            {doc.file_url ? 'Uploaded' : 'Missing'}
                          </Text>
                        </XStack>
                      </XStack>
                    </React.Fragment>
                  ))}
                </Card>
              </YStack>
            ) : null}

            {/* Quick links */}
            <YStack marginHorizontal={16} marginTop={20} gap={8}>
              <QuickLink
                label="Attendance History"
                onPress={() => (navigation as any).getParent()?.navigate('AttendanceTab')}
              />
              <QuickLink
                label="My Issues"
                onPress={() => (navigation as any).getParent()?.navigate('HomeTab', { screen: 'Issues' })}
              />
              <QuickLink
                label="Manage Availability"
                onPress={() => navigation.navigate('Availability')}
              />
            </YStack>

          </YStack>
        </ScrollView>
      )}
    </View>
  );
}

/* ── Sub-components ────────────────────────────────────── */

function InfoCard({ children }: { children: React.ReactNode }) {
  return (
    <YStack
      backgroundColor={C.card}
      borderRadius={14}
      borderWidth={1}
      borderColor={C.neutral200}
      overflow="hidden"
    >
      {children}
    </YStack>
  );
}

function InfoRow({
  label,
  value,
  icon,
  mono = false,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <XStack paddingHorizontal={16} paddingVertical={14} alignItems="center" gap={10}>
      {icon ? <View width={20} alignItems="center">{icon}</View> : null}
      <Text fontSize={13} color={C.neutral500} flex={1}>{label}</Text>
      <Text
        fontSize={13}
        fontWeight="500"
        color={C.neutral900}
        fontFamily={mono ? "$mono" : undefined}
        textAlign="right"
        flex={1}
      >
        {value}
      </Text>
    </XStack>
  );
}

function Divider() {
  return <View height={1} backgroundColor={C.neutral200} />;
}

function SectionLabel({ label, icon }: { label: string; icon?: React.ReactNode }) {
  return (
    <XStack alignItems="center" gap={6}>
      {icon}
      <Text fontSize={11} fontWeight="600" color={C.neutral500} letterSpacing={1}>
        {label}
      </Text>
    </XStack>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "long", year: "numeric" }).format(
    new Date(value),
  );
}

function formatDocType(type: string) {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function QuickLink({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Button
      height={52}
      borderRadius={14}
      backgroundColor={C.card}
      borderWidth={1}
      borderColor={C.neutral200}
      pressStyle={{ backgroundColor: '#FAFAF9', scale: 0.99 }}
      onPress={onPress}
    >
      <XStack flex={1} alignItems="center" justifyContent="space-between">
        <Text fontSize={14} fontWeight="500" color={C.neutral900}>{label}</Text>
        <ChevronRight size={16} color={C.neutral500} />
      </XStack>
    </Button>
  );
}
