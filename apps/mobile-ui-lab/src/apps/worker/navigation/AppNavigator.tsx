import React from 'react';
import { Platform } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { House, Briefcase, ClipboardList, DollarSign, User } from 'lucide-react-native';

import HomeScreen from '../screens/HomeScreen';
import JobsBoardScreen from '../screens/JobsBoardScreen';
import JobDetailScreen from '../screens/JobDetailScreen';
import AvailabilityScreen from '../screens/AvailabilityScreen';
import AttendanceHistoryScreen from '../screens/AttendanceHistoryScreen';
import EarningsScreen from '../screens/EarningsScreen';
import PaymentScreen from '../screens/PaymentScreen';
import ProfileScreen from '../screens/ProfileScreen';
import IssuesScreen from '../screens/IssuesScreen';
import RaiseIssueScreen from '../screens/RaiseIssueScreen';
import IssueDetailScreen from '../screens/IssueDetailScreen';

import type {
  WorkerTabParamList,
  HomeStackParamList,
  JobsStackParamList,
  AttendanceStackParamList,
  EarningsStackParamList,
  ProfileStackParamList,
} from './types';

const Tab = createBottomTabNavigator<WorkerTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const JobsStack = createNativeStackNavigator<JobsStackParamList>();
const AttendanceStack = createNativeStackNavigator<AttendanceStackParamList>();
const EarningsStack = createNativeStackNavigator<EarningsStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();

const C = {
  brand600: '#1A6640',
  brand900: '#0D2E1E',
  neutral500: '#78716C',
  card: '#FFFFFF',
  neutral200: '#E7E5E4',
};

function HomeStackNavigator() {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="Home" component={HomeScreen} />
      <HomeStack.Screen name="Issues" component={IssuesScreen} />
      <HomeStack.Screen name="RaiseIssue" component={RaiseIssueScreen} />
      <HomeStack.Screen name="IssueDetail" component={IssueDetailScreen} />
      <HomeStack.Screen name="JobDetail" component={JobDetailScreen} />
    </HomeStack.Navigator>
  );
}

function JobsStackNavigator() {
  return (
    <JobsStack.Navigator screenOptions={{ headerShown: false }}>
      <JobsStack.Screen name="Jobs" component={JobsBoardScreen} />
      <JobsStack.Screen name="JobDetail" component={JobDetailScreen} />
    </JobsStack.Navigator>
  );
}

function AttendanceStackNavigator() {
  return (
    <AttendanceStack.Navigator screenOptions={{ headerShown: false }}>
      <AttendanceStack.Screen name="AttendanceHistory" component={AttendanceHistoryScreen} />
    </AttendanceStack.Navigator>
  );
}

function EarningsStackNavigator() {
  return (
    <EarningsStack.Navigator screenOptions={{ headerShown: false }}>
      <EarningsStack.Screen name="Earnings" component={EarningsScreen} />
      <EarningsStack.Screen name="Payments" component={PaymentScreen} />
    </EarningsStack.Navigator>
  );
}

function ProfileStackNavigator() {
  return (
    <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
      <ProfileStack.Screen name="Profile" component={ProfileScreen} />
      <ProfileStack.Screen name="Availability" component={AvailabilityScreen} />
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
          if (route.name === 'AttendanceTab') return <ClipboardList size={size} color={color} />;
          if (route.name === 'EarningsTab') return <DollarSign size={size} color={color} />;
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
        name="AttendanceTab"
        component={AttendanceStackNavigator}
        options={{ tabBarLabel: 'Attendance' }}
      />
      <Tab.Screen
        name="EarningsTab"
        component={EarningsStackNavigator}
        options={{ tabBarLabel: 'Earnings' }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileStackNavigator}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
}
