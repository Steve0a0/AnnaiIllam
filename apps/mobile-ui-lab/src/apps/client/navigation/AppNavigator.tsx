import { useEffect, useState } from 'react';
import { Platform, View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { House, MessageCircleWarning, User } from 'lucide-react-native';

import HomeScreen from '../screens/HomeScreen';
import CreateRequestScreen from '../screens/CreateRequestScreen';
import RequestDetailScreen from '../screens/RequestDetailScreen';
import AssignedWorkersScreen from '../screens/AssignedWorkersScreen';
import RequestsScreen from '../screens/RequestsScreen';
import ComplaintsScreen from '../screens/ComplaintsScreen';
import RaiseComplaintScreen from '../screens/RaiseComplaintScreen';
import ComplaintDetailScreen from '../screens/ComplaintDetailScreen';
import ClientProfileScreen, { AddPhoneSheet } from '../screens/ClientProfileScreen';
import BillingOverviewScreen from '../screens/BillingOverviewScreen';
import InvoiceViewerScreen from '../screens/InvoiceViewerScreen';
import InvoiceDetailScreen from '../screens/InvoiceDetailScreen';
import PaymentConfirmScreen from '../screens/PaymentConfirmScreen';
import RateRequirementScreen from '../screens/RateRequirementScreen';
import DisputeScreen from '../screens/DisputeScreen';
import { clientProfileService } from '../../../shared/services/client-profile.service';
import { useAuthStore } from '../../../shared/store/auth.store';

import type {
  ClientTabParamList,
  HomeStackParamList,
  ComplaintsStackParamList,
  ProfileStackParamList,
} from './types';

const Tab = createBottomTabNavigator<ClientTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const ComplaintsStack = createNativeStackNavigator<ComplaintsStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();

const C = {
  brand600: '#1A6640',
  neutral500: '#78716C',
  card: '#FFFFFF',
  neutral200: '#E7E5E4',
};

function HomeStackNavigator() {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="Home" component={HomeScreen} />
      <HomeStack.Screen name="AllRequests" component={RequestsScreen} />
      <HomeStack.Screen name="CreateRequest" component={CreateRequestScreen} />
      <HomeStack.Screen name="RequestDetail" component={RequestDetailScreen} />
      <HomeStack.Screen name="AssignedWorkers" component={AssignedWorkersScreen} />
      <HomeStack.Screen name="RaiseComplaint" component={RaiseComplaintScreen} />
      <HomeStack.Screen name="InvoiceDetail" component={InvoiceDetailScreen} />
      <HomeStack.Screen name="PaymentConfirm" component={PaymentConfirmScreen} />
      <HomeStack.Screen name="RateRequirement" component={RateRequirementScreen} />
      <HomeStack.Screen name="RaiseDispute" component={DisputeScreen} />
    </HomeStack.Navigator>
  );
}

function ComplaintsStackNavigator() {
  return (
    <ComplaintsStack.Navigator screenOptions={{ headerShown: false }}>
      <ComplaintsStack.Screen name="Complaints" component={ComplaintsScreen} />
      <ComplaintsStack.Screen name="RaiseComplaint" component={RaiseComplaintScreen} />
      <ComplaintsStack.Screen name="ComplaintDetail" component={ComplaintDetailScreen} />
    </ComplaintsStack.Navigator>
  );
}

function ProfileStackNavigator() {
  return (
    <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
      <ProfileStack.Screen name="ClientProfile" component={ClientProfileScreen} />
      <ProfileStack.Screen name="BillingOverview" component={BillingOverviewScreen} />
      <ProfileStack.Screen name="InvoiceViewer" component={InvoiceViewerScreen} />
    </ProfileStack.Navigator>
  );
}

export default function AppNavigator() {
  const user = useAuthStore((s) => s.user);
  const [needsPhone, setNeedsPhone] = useState(false);

  useEffect(() => {
    let active = true;

    const checkPhone = async () => {
      if (user?.phone) {
        setNeedsPhone(false);
        return;
      }

      try {
        const profile = await clientProfileService.getProfile();
        if (active) setNeedsPhone(!profile.phone);
      } catch {
        if (active) setNeedsPhone(false);
      }
    };

    checkPhone();

    return () => {
      active = false;
    };
  }, [user?.phone]);

  return (
    <View style={{ flex: 1 }}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: C.card,
            borderTopColor: C.neutral200,
            borderTopWidth: 0.5,
            height: Platform.OS === 'ios' ? 84 : 64,
            paddingBottom: Platform.OS === 'ios' ? 28 : 10,
            paddingTop: 8,
          },
          tabBarActiveTintColor: C.brand600,
          tabBarInactiveTintColor: C.neutral500,
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '500',
          },
          tabBarIcon: ({ color, size }) => {
            if (route.name === 'HomeTab') return <House size={size} color={color} />;
            if (route.name === 'ComplaintsTab') return <MessageCircleWarning size={size} color={color} />;
            if (route.name === 'ProfileTab') return <User size={size} color={color} />;
            return null;
          },
        })}
      >
        <Tab.Screen
          name="HomeTab"
          component={HomeStackNavigator}
          options={{ tabBarLabel: 'Home' }}
        />
        <Tab.Screen
          name="ComplaintsTab"
          component={ComplaintsStackNavigator}
          options={{ tabBarLabel: 'Complaints' }}
        />
        <Tab.Screen
          name="ProfileTab"
          component={ProfileStackNavigator}
          options={{ tabBarLabel: 'Profile' }}
        />
      </Tab.Navigator>

      <AddPhoneSheet
        visible={needsPhone}
        required
        title="Verify phone number"
        subtitle="Add your mobile number to secure this account and receive job updates. We will send a 6-digit OTP to verify it."
        onClose={() => undefined}
        onSaved={() => setNeedsPhone(false)}
      />
    </View>
  );
}
