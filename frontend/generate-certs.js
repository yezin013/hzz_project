const forge = require('node-forge');
const fs = require('fs');
const path = require('path');

const certsDir = path.join(__dirname, 'certs');

// Create certs directory if it doesn't exist
if (!fs.existsSync(certsDir)) {
    fs.mkdirSync(certsDir, { recursive: true });
}

const certPath = path.join(certsDir, 'cert.pem');
const keyPath = path.join(certsDir, 'key.pem');

// Check if certificates already exist
if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
    console.log('SSL certificates already exist.');
    process.exit(0);
}

console.log('Generating self-signed SSL certificate...');

// Generate a key pair
const keys = forge.pki.rsa.generateKeyPair(2048);

// Create a certificate
const cert = forge.pki.createCertificate();
cert.publicKey = keys.publicKey;
cert.serialNumber = '01';
cert.validity.notBefore = new Date();
cert.validity.notAfter = new Date();
cert.validity.notAfter.setFullYear(cert.validity.notBefore.getFullYear() + 1);

const attrs = [{
    name: 'commonName',
    value: '192.168.0.48'
}, {
    name: 'countryName',
    value: 'KR'
}, {
    shortName: 'ST',
    value: 'Seoul'
}, {
    name: 'localityName',
    value: 'Seoul'
}, {
    name: 'organizationName',
    value: 'Local Development'
}];

cert.setSubject(attrs);
cert.setIssuer(attrs);

cert.setExtensions([{
    name: 'basicConstraints',
    cA: true
}, {
    name: 'keyUsage',
    keyCertSign: true,
    digitalSignature: true,
    nonRepudiation: true,
    keyEncipherment: true,
    dataEncipherment: true
}, {
    name: 'subjectAltName',
    altNames: [{
        type: 7, // IP
        ip: '192.168.0.48'
    }, {
        type: 2, // DNS
        value: 'localhost'
    }]
}]);

// Self-sign certificate
cert.sign(keys.privateKey, forge.md.sha256.create());

// Convert to PEM format
const pemCert = forge.pki.certificateToPem(cert);
const pemKey = forge.pki.privateKeyToPem(keys.privateKey);

// Save to files
fs.writeFileSync(certPath, pemCert);
fs.writeFileSync(keyPath, pemKey);

console.log('✅ SSL certificates generated successfully!');
console.log(`   Certificate: ${certPath}`);
console.log(`   Private Key: ${keyPath}`);
