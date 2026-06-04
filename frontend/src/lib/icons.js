/**
 * Phosphor → lucide shim. Drop-in replacement.
 * Replace imports `from "@/lib/icons"` with `from "@/lib/icons"`.
 * Maps the Phosphor `weight` prop to lucide `strokeWidth`.
 */
import React from "react";
import {
  ArrowRight as LArrowRight, ArrowLeft as LArrowLeft,
  Download, ChevronLeft, ChevronRight, Search,
  SkipForward as LSkipForward, RotateCcw, RefreshCw,
  Square, Pause as LPause, Play as LPlay,
  MessageCircle, FileText as LFileText, Mail, Target as LTarget,
  Headset as LHeadset, Settings, Plus as LPlus, Check as LCheck,
  Copy as LCopy, Trash2,
  Truck as LTruck, Wrench as LWrench, Stethoscope as LStethoscope,
  Code as LCode, ShoppingBag as LShoppingBag, Briefcase as LBriefcase,
  Gavel as LGavel, Building2,
  Bot, User as LUser, Quote,
  Zap, Lock as LLock, TrendingUp, BarChart,
  Users as LUsers, Clock as LClock, MapPin as LMapPin,
  Database as LDatabase, Webhook, LifeBuoy as LLifeBuoy,
  Presentation, CheckCircle2, XCircle as LXCircle,
  Phone, Linkedin,
} from "lucide-react";

const weightToStroke = (weight) => {
  if (weight === "bold") return 2.5;
  if (weight === "light") return 1.25;
  if (weight === "thin") return 1;
  return 2;
};

const wrap = (Comp) => {
  const C = ({ weight, ...rest }) => <Comp strokeWidth={weightToStroke(weight)} {...rest} />;
  C.displayName = `Icon(${Comp.displayName || Comp.name || "x"})`;
  return C;
};

// Named exports — Phosphor identifiers on the left, lucide components on the right
export const ArrowRight        = wrap(LArrowRight);
export const ArrowLeft         = wrap(LArrowLeft);
export const ArrowUpRight      = wrap(LArrowRight);
export const DownloadSimple    = wrap(Download);
export const CaretLeft         = wrap(ChevronLeft);
export const CaretRight        = wrap(ChevronRight);
export const MagnifyingGlass   = wrap(Search);
export const SkipForward       = wrap(LSkipForward);
export const ArrowClockwise    = wrap(RotateCcw);
export const ArrowsClockwise   = wrap(RefreshCw);
export const Stop              = wrap(Square);
export const Pause             = wrap(LPause);
export const Play              = wrap(LPlay);
export const ChatCircle        = wrap(MessageCircle);
export const FileText          = wrap(LFileText);
export const EnvelopeSimple    = wrap(Mail);
export const Target            = wrap(LTarget);
export const Headset           = wrap(LHeadset);
export const GearSix           = wrap(Settings);
export const Plus              = wrap(LPlus);
export const Check             = wrap(LCheck);
export const Copy              = wrap(LCopy);
export const TrashSimple       = wrap(Trash2);
export const Truck             = wrap(LTruck);
export const Wrench            = wrap(LWrench);
export const Stethoscope       = wrap(LStethoscope);
export const Heartbeat         = wrap(LStethoscope);
export const Code              = wrap(LCode);
export const ShoppingBag       = wrap(LShoppingBag);
export const Briefcase         = wrap(LBriefcase);
export const Gavel             = wrap(LGavel);
export const Buildings         = wrap(Building2);
export const Building          = wrap(Building2);
export const Robot             = wrap(Bot);
export const User              = wrap(LUser);
export const Quotes            = wrap(Quote);
export const Lightning         = wrap(Zap);
export const Lock              = wrap(LLock);
export const ChartLineUp       = wrap(TrendingUp);
export const ChartBar          = wrap(BarChart);
export const Users             = wrap(LUsers);
export const Clock             = wrap(LClock);
export const MapPin            = wrap(LMapPin);
export const Database          = wrap(LDatabase);
export const Webhooks          = wrap(Webhook);
export const Lifebuoy          = wrap(LLifeBuoy);
export const PresentationChart = wrap(Presentation);
export const CheckCircle       = wrap(CheckCircle2);
export const XCircle           = wrap(LXCircle);
export const Files             = wrap(LFileText);
export const PhoneCall         = wrap(Phone);
export const LinkedinLogo      = wrap(Linkedin);
