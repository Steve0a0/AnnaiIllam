import { Platform } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Briefcase, House, MessageCircleWarning, User } from 'lucide-react-native';

import HomeScreen from '../screens/HomeScreen';
import CreateRequestScreen from '../screens/CreateRequestScreen';
import RequestDetailScreen from '../screens/RequestDetailScreen';
import AssignedWorkersScreen from '../screens/AssignedWorkersScreen';
import RequestsScreen from '../screens/RequestsScreen';
import ComplaintsScreen from '../screens/ComplaintsScreen';
import RaiseComplaintScreen from '../screens/RaiseComplaintScreen';
import ComplaintDetailScreen from '../screens/ComplaintDetailScreen';
import ClientProfileScreen from '../screens/ClientProfileScreen';
import InvoiceDetailScreen from '../screens/InvoiceDetailScreen';
import PaymentConfirmScreen from '../screens/PaymentConfirmScreen';
import RateRequirementScreen from '../screens/RateRequirementScreen';

import type {
  ClientTabParamList,
  HomeStackParamList,
  JobsStackParamList,
  ComplaintsStackParamList,
  ProfileStackParamList,
} from './types';

const Tab = createBottomTabNavigator<ClientTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const JobsStack = createNativeStackNavigator<JobsStackParamList>();
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
      <HomeStack.Screen name="CreateRequest" component={CreateRequestScreen} />
      <HomeStack.Screen name="RequestDetail" component={RequestDetailScreen} />
      <HomeStack.Screen name="AssignedWorkers" component={AssignedWorkersScreen} />
      <HomeStack.Screen name="RaiseComplaint" component={RaiseComplaintScreen} />
      <HomeStack.Screen name="InvoiceDetail" component={InvoiceDetailScreen} />
      <HomeStack.Screen name="PaymentConfirm" component={PaymentConfirmScreen} />
      <HomeStack.Screen name="RateRequirement" component={RateRequirementScreen} />
    </HomeStack.Navigator>
  );
}

function JobsStackNavigator() {
  return (
    <JobsStack.Navigator screenOptions={{ headerShown: false }}>
      <JobsStack.Screen name="Requests" component={RequestsScreen} />
      <JobsStack.Screen name="CreateRequest" component={CreateRequestScreen} />
      <JobsStack.Screen name="RequestDetail" component={RequestDetailScreen} />
      <JobsStack.Screen name="AssignedWorkers" component={AssignedWorkersScreen} />
      <JobsStack.Screen name="RaiseComplaint" component={RaiseComplaintScreen} />
      <JobsStack.Screen name="InvoiceDetail" component={InvoiceDetailScreen} />
      <JobsStack.Screen name="PaymentConfirm" component={PaymentConfirmScreen} />
      <JobsStack.Screen name="RateRequirement" component={RateRequirementScreen} />
    </JobsStack.Navigator>
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
    </ProfileStack.Navigator>
  );
}

export default function AppNavigator() {
  return (
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
          if (route.name === 'JobsTab') return <Briefcase size={size} color={color} />;
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
        name="JobsTab"
        component={JobsStackNavigator}
        options={{ tabBarLabel: 'Jobs' }}
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
  );
}
