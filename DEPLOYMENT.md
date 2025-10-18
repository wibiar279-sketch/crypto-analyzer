# Panduan Deployment Crypto Analyzer

## 🚀 Deployment Options

### Option 1: Local Development Server (Recommended for Testing)

1. **Setup Backend**
```bash
cd crypto_analyzer
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Run Server**
```bash
python wsgi.py
```

3. **Access**
- URL: http://localhost:5000
- API: http://localhost:5000/api/health

### Option 2: Production Deployment

#### A. Using Gunicorn (Recommended)

1. **Install Gunicorn**
```bash
pip install gunicorn
```

2. **Run with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

3. **With Nginx (Optional)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### B. Using Docker

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

2. **Build and Run**
```bash
docker build -t crypto-analyzer .
docker run -p 5000:5000 crypto-analyzer
```

#### C. Deploy to Cloud Platforms

**Heroku:**
```bash
# Install Heroku CLI
heroku login
heroku create crypto-analyzer-app
git push heroku main
```

**Railway:**
1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn wsgi:app`

**Render:**
1. Connect repository
2. Set environment: Python 3.11
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn wsgi:app`

## 🔧 Environment Variables

Create `.env` file (optional):
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
```

## 📊 Performance Optimization

### 1. Caching
The app already implements caching with 10-second timeout. Adjust in `indodax_service.py`:
```python
self._cache_timeout = 10  # seconds
```

### 2. Rate Limiting
Indodax API limit: 180 requests/minute
- Dashboard uses ~3 requests per load
- Detail page uses ~4 requests per crypto
- Auto-refresh every 30 seconds

### 3. Database (Optional)
For production, consider adding PostgreSQL for:
- User accounts
- Favorite cryptocurrencies
- Alert notifications
- Historical analysis data

## 🔒 Security Considerations

1. **API Keys**: If using private API, store in environment variables
2. **CORS**: Already configured for all origins (adjust for production)
3. **HTTPS**: Use SSL certificate in production
4. **Rate Limiting**: Implement server-side rate limiting

## 📈 Monitoring

### Health Check
```bash
curl http://your-domain.com/api/health
```

Expected response:
```json
{"status":"ok","service":"Crypto Analyzer API"}
```

### Logs
```bash
# View Flask logs
tail -f /var/log/crypto-analyzer/app.log

# View Gunicorn logs
tail -f /var/log/crypto-analyzer/gunicorn.log
```

## 🐛 Troubleshooting

### Issue: Port already in use
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Issue: Module import errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Issue: API timeout
- Check internet connection
- Verify Indodax API is accessible
- Increase timeout in `indodax_service.py`

### Issue: Frontend not loading
```bash
# Rebuild frontend
cd crypto-analyzer-frontend
pnpm run build
cp -r dist/* ../crypto_analyzer/src/static/
```

## 🔄 Updates & Maintenance

### Update Dependencies
```bash
# Backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Frontend
cd crypto-analyzer-frontend
pnpm update
```

### Database Migrations (if using)
```bash
flask db upgrade
```

### Backup
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz crypto_analyzer/

# Backup database (if using)
pg_dump crypto_analyzer > backup.sql
```

## 📞 Support

For issues or questions:
1. Check logs first
2. Verify API connectivity
3. Test with health check endpoint
4. Review error messages

## 🎯 Next Steps

After deployment:
1. Test all features thoroughly
2. Monitor API usage and rate limits
3. Set up automated backups
4. Configure monitoring and alerts
5. Optimize caching strategy
6. Consider adding user authentication
7. Implement email/telegram notifications for price alerts

---

**Happy Trading! 📈💰**

