# BMI Hesaplama Uygulaması - BSM359 Final Projesi

Öğrenci Adı: Sümeyye Çakır  
Öğrenci Numarası:23010310021  
Ders:BSM359 - Bulut Bilişim  
Teslim Tarihi:20 Mayıs 2026  

## 1. Proje Özeti

Bu proje, kullanıcıların Vücut Kitle İndeksi (BMI) hesaplamasını yapabildiği, hesaplama sonuçlarını kalıcı olarak saklayan ve geçmiş hesaplamalarını görüntüleyebildiği
bir web uygulamasını kapsamaktadır. Uygulama, Docker ile container hale getirilmiş ve Google Kubernetes Engine (GKE) üzerinde çalışacak şekilde yapılandırılmıştır.

Proje kapsamında aşağıdaki Kubernetes özellikleri kullanılmıştır:
- Deployment ile 2 replica çalıştırma ve RollingUpdate stratejisi
- LoadBalancer tipinde Service ile dış dünyaya açılma
- StatefulSet ile MySQL veritabanı yönetimi
- Persistent Volume Claim (PVC) ile 2GB kalıcı depolama
- NetworkPolicy ile güvenli erişim kontrolü
- Secret ile hassas verilerin güvenli saklanması
- Manual Scaling (ölçekleme) işlemleri
- Rolling update ve rollback mekanizmaları
- Cloud Build ile CI/CD pipeline
---
## 2. Teknoloji Stack

| Bileşen        | Teknoloji                  | Açıklama |
|---------       |-----------                 |----------|
| Backend        | Flask (Python)             | Web framework, BMI hesaplama ve REST API 
| Database       | MySQL 8.0                  | Veri saklama (bmi_records tablosu) 
| Container      | Docker                     | Uygulamanın containerization işlemi 
| Orchestration  | Kubernetes (GKE)           | Container yönetimi ve scaling 
| CI/CD          | Google Cloud Build         | Otomatik build ve deploy pipeline 
| Image Storage  | Artifact Registry          | Docker imajlarının saklanması 
| Load Balancing | Google Cloud Load Balancer | Dış trafiği uygulamaya yönlendirme 

---
## 3. Uygulama Mimarisi

Uygulama üç ana katmandan oluşmaktadır:

### 3.1 Sunum Katmanı (Presentation Layer)
HTML, CSS ve JavaScript ile oluşturulan kullanıcı arayüzüdür. Kullanıcıdan kilo ve boy bilgilerini alır, BMI hesaplama sonucunu ve geçmiş hesaplamaları gösterir.

### 3.2 İş Katmanı (Business Layer)
Flask framework ile yazılmış backend uygulamasıdır. BMI hesaplama formülünü (kilo / (boy/100)²) uygular, sonuca göre kategori belirler (Zayıf, Normal, Kilolu, Obez) ve
REST API endpoint'lerini sağlar.

### 3.3 Veri Katmanı (Data Layer)
MySQL veritabanından oluşur. bmi_records tablosu içerisinde id, weight, height, bmi, category ve created_at alanlarını barındırır. 
StatefulSet ve PVC ile kalıcı depolama sağlanmıştır.

---

## 4. Sistem Mimarisi

### 4.1 Teknoloji Bileşenleri
- Flask:Port 5000'de çalışan web framework, BMI hesaplama yapar.
- MySQL: Port 3306'da çalışan veritabanı, hesaplama sonuçlarını saklar.
- Docker:Uygulamayı container haline getirir.
- GKE: Kubernetes orchestration sağlar (cluster: bmi-cluster, zone: europe-west1-b).
- Cloud Build: CI/CD pipeline (main branch trigger, cloudbuild.yaml config).

### 4.2 Google Cloud Servisleri
- Artifact Registry: Docker imajlarının saklandığı repo (bmi-repo, region: europe-west1).
- Load Balancing:External IP 34.53.190.118 üzerinden 80 portunu 5000'e yönlendirir.

### 4.3 Sistem Akışı
1. Geliştirici kodu GitHub'a push eder.
2. Cloud Build tetiklenir ve Docker imajı oluşturur.
3. İmaj Artifact Registry'ye push edilir.
4. GKE cluster imajı çeker ve rolling update yapar.
5. Load Balancer trafiği uygulamaya yönlendirir.
6. Kullanıcılar http://34.53.190.118 adresinden uygulamaya erişir.

---

## 5. Kubernetes Mimarisi

### 5.1 GKE Control Plane (Google tarafından yönetilir)
- API Server:Tüm API isteklerini karşılar.
- Scheduler:Pod'ları node'lara yerleştirir.
- Controller Manager:Deployment ve ReplicaSet'leri yönetir.
- etcd: Cluster veri deposu.

### 5.2 Worker Node'lar
- Sayı: 2 node
- Tip: e2-small
- Zone: europe-west1-b

### 5.3 Namespace
Tüm kaynaklar `bmi-app` namespace'i altında toplanmıştır.

### 5.4 Deployment (bmi-deployment)
- **replicas:** 2
- **strategy:** RollingUpdate
- **rollingUpdate.maxSurge:** 1
- **rollingUpdate.maxUnavailable:** 0
- **resources.requests:** CPU 100m, Memory 128Mi
- **resources.limits:** CPU 500m, Memory 256Mi
- **livenessProbe & readinessProbe:** /health endpoint

### 5.5 Service
- bmi-app-service (LoadBalancer): External IP 34.53.190.118, Port 80 → 5000
- bmi-db-service (ClusterIP):Port 3306

### 5.6 StatefulSet ve PVC
- StatefulSet:bmi-db-stateful (1 replica, MySQL 8.0)
- PVC: db-storage, 2Gi, ReadWriteOnce, mount path: /var/lib/mysql

### 5.7 NetworkPolicy
- bmi-network-policy: Sadece app=bmi-app pod'larının MySQL'e (port 3306) erişmesine izin verir.

### 5.8 Secret
- bmi-db-secret: MYSQL_ROOT_PASSWORD (bmi123) ve MYSQL_DATABASE (bmidb)

---

## 6. CI/CD Pipeline Akışı

### 6.1 Geliştirici Akışı
1. Kod yaz (app.py'de değişiklik)
2. git add .
3. git commit -m "v2.0"
4. git push origin main

### 6.2 GitHub Repository
- **URL:** https://github.com/sumeyyecakir06/bmi-mysql-app
- main branch'e push algılanır → Webhook tetiklenir → Cloud Build Trigger devreye girer

### 6.3 Cloud Build Pipeline (5 Adım)
1. Docker Build: docker build -t europe-west1-docker.pkg.dev/bmi-final-proje/bmi-repo/bmi-app:$COMMIT_SHA .
2. Docker Push: docker push .../bmi-app:$COMMIT_SHA
3. GKE Bağlantı:gcloud container clusters get-credentials bmi-cluster --zone=europe-west1-b
4. Rolling Update: kubectl set image deployment/bmi-deployment bmi-app=.../$COMMIT_SHA -n bmi-app
5. Rollout Status: kubectl rollout status deployment/bmi-deployment -n bmi-app --timeout=5m

### 6.4 Sonuç
Yeni versiyon uygulama kesintisi olmadan yayına alınır ve kullanıcılar http://34.53.190.118 adresinden erişebilir.

---

## 7. Rolling Update, Rollback ve Ölçekleme

### 7.1 Rolling Update (Kesintisiz Güncelleme)

kubectl set image deployment/bmi-deployment bmi-app=europe-west1-docker.pkg.dev/bmi-final-proje/bmi-repo/bmi-app:v2.0 -n bmi-app
kubectl rollout status deployment/bmi-deployment -n bmi-app

### 7.2 Rollback (Geri Alma)

kubectl rollout undo deployment/bmi-deployment -n bmi-app
kubectl rollout status deployment/bmi-deployment -n bmi-app

### 7.3 Manuel Ölçekleme (Scaling)

kubectl scale deployment bmi-deployment --replicas=4 -n bmi-app
kubectl get pods -n bmi-app
kubectl scale deployment bmi-deployment --replicas=2 -n bmi-app
