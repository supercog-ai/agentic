import { type ClassValue,clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

import { AgentEventType } from '@/lib/api';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const convertFromUTC = (dateString: string): Date => {
  const date = new Date(dateString);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60 * 1000);
};

export const formatDate = (date: string | Date, convertToLocale: boolean = false, includeSeconds: boolean = false): string => {
  const dateString = typeof date === 'string' ? date : date.toISOString();
  const localDate = convertToLocale ? convertFromUTC(dateString) : new Date(dateString);
  const month = localDate.toLocaleString('en-US', { month: 'short' });
  const day = localDate.getDate();
  const suffix = ['th', 'st', 'nd', 'rd'][(day % 10 > 3 ? 0 : day % 10)] || 'th';
  const time = localDate.toLocaleString('en-US', { 
    hour: 'numeric',
    minute: '2-digit',
    second: includeSeconds ? '2-digit' : undefined,
    hour12: true
  }).toLowerCase();
  
  return `${month} ${day}${suffix}, ${time}`;
};

export const isUserTurn = (agentName: string, event: Api.AgentEvent): boolean => {
  const isTerminationEvent = event.type === AgentEventType.TURN_END || event.type === AgentEventType.TURN_CANCELLED || event.type === AgentEventType.WAIT_FOR_INPUT;
  return isTerminationEvent && agentName === event.agent;
};
