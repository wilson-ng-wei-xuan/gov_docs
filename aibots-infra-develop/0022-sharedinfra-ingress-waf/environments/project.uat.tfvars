# update your project specific environmental

retention_in_days = 365

whitelisted_ips = {
  # SIS / GoMax
  # See Hian CHUA <CHUA_See_Hian@tech.gov.sg>
  # Chee Tiong KEAK <KEAK_Chee_Tiong@tech.gov.sg>
  # Edmund CHEW <Edmund_CHEW@tech.gov.sg>, Linda LIM <Linda_LIM@tech.gov.sg>
  "sis_gomax" : [
    "57.140.27.13/32",  # sis gomax ip
  ],
  "sis_gomax_v6" : [
  ],

  # SEED
  # Hunter
  "seed" : [
    "8.29.230.18/32",
    "8.29.230.19/32",
  ],
  "seed_v6" : [
    "2a09:bac0:1000:20::279:ad/128",
    "2a09:bac0:1000:20::278:64/127"
  ],

  # Ngee Ann Poly
  # Eugene ANG <Eugene_ANG@np.edu.sg>
  # Terence CHAN (NP) <Terence_CHAN@np.edu.sg>
  "np" : [
    "153.20.24.195/32",
    "153.20.79.99/32",
    "153.20.79.200/32",
    "153.20.91.85/32",
    "153.20.92.86/32",
    "130.41.227.249/32",
    "130.41.227.250/32",
    "140.209.206.6/32",
    "140.209.206.102/32"
  ],
  "np_v6" : [
  ],

  # SP
  # Kenny SEAH <Kenny_SEAH@sp.edu.sg>
  # Jason TSENG <Jason_TSENG@sp.edu.sg>
  "sp" : [
    "164.78.250.101/32",
    "164.78.250.102/32",
    "164.78.248.70/32",
    "164.78.248.200/32",
    "164.78.248.244/32",
    "164.78.252.70/32",
    "164.78.252.200/32",
    "164.78.252.244/32",
  ],
  "sp_v6" : [
  ],

  # RP
  # Stella Tew (RP) <stella_tew@RP.EDU.SG>
  # Chong Hui Miin (RP) <chong_hui_miin2@rp.edu.sg>
  "rp" : [
    "165.85.9.244/32",
    "165.85.9.245/32",
    "202.21.159.215/32",
    "202.21.159.251/32",
    "202.21.159.252/32", # Morgan Heijdemann (RP) <morgan_heijdemann@rp.edu.sg>
  ],
  "rp_v6" : [
  ],

  # NYP
  # Francis Lee (NYP) <francis_lee@nyp.edu.sg>
  "nyp" : [
    "57.140.27.56/32",
    "202.12.95.96/32",
  ],
  "nyp_v6" : [
  ],

  # ITE
  # Kravitz HWANG <kravitz_j_h_hwang@ite.edu.sg> Deputy Director/Digitalisation Office
  # Chee Wai SOONG <Soong_Chee_Wai@ite.edu.sg> Senior Head/Network Architecture, IT Division
  # Choon Chiat TAN <Tan_Choon_Chiat@ite.edu.sg>; Ricky TAN <ricky_tan@ite.edu.sg>; Sourirajan KRISHNASAMY <Sourirajan_Krishnasamy@ite.edu.sg>
  "ite" : [
    "182.54.229.11/32",
    "182.54.229.12/32",
    "182.54.229.13/32",
    "182.54.229.14/32",
    "182.54.229.15/32",
    "182.54.229.16/32",
    "182.54.229.17/32",
    "182.54.229.18/32",
    "182.54.229.19/32",
    "182.54.229.20/32",
    "182.54.229.21/32",
    "182.54.229.22/32",
    "182.54.229.23/32",
    "182.54.229.24/32",
    "182.54.229.25/32",
    "182.54.231.25/32",
    "182.54.231.39/32",
    "182.54.231.40/32",
    "182.54.231.54/32",
    "182.54.231.81/32",
    "103.196.112.11/32",
    "103.196.112.12/32",
    "103.196.112.13/32",
    "103.196.114.117/32",
    "103.196.114.119/32",
    "103.196.114.120/32",
    "103.196.114.121/32",
    "103.196.114.123/32",
    "103.196.114.125/32",
    "103.196.114.127/32",
  ],
  "ite_v6" : [
  ],

  # MOE
  # Soon Lan LEE <LEE_Soon_Lan@tech.gov.sg>
  # Rong CONG <Rong_CONG@moe.gov.sg>; Dylan KONG <Dylan_KONG@tech.gov.sg>; Jian Ling WU <WU_Jian_Ling@tech.gov.sg>; Tai Seng NG <NG_Tai_Seng@moe.gov.sg>
  "moe" : [
    "129.126.33.0/24",
    "129.126.34.0/24",
    "129.126.37.0/24",
    "129.126.38.0/24",
  ],
  "moe_v6" : [
  ],

  # SINGAPORE SPORTS SCHOOL
  # Jackson Tong <jacksontong@sportsschool.edu.sg>
  "sportschool" : [
    "66.96.214.196/32",
    "66.96.214.180/32",
    "165.175.10.30/32",
    "180.255.74.70/32",
  ],
  "sportschool_v6" : [
  ],

  # MINDEF
  # Joel LEONG <Leong_Yaw_Wenn_Joel@mindef.gov.sg>
  # Ow Hong Cheng <OHONGCHE@dsta.gov.sg>, Goh Wei Li Jermie <GWEILIJE@dsta.gov.sg>
  "mindef" : [
    "57.140.27.174/32",
    "117.20.136.96/27",
    "118.201.51.224/27",
  ],
  "mindef_v6" : [
  ],

  # NHG
  # Er Chuan Teck (NHGHQ) <Chuan_Teck_Er@nhg.com.sg>, Fritzie Buizon (Synapxe) <buizon.ma.fritzie@synapxe.sg>
  "nhg": [
    "57.140.27.199/32"
  ],
  "nhg_v6": [
  ],
}