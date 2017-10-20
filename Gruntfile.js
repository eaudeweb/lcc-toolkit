module.exports = function(grunt) {
    require('jit-grunt')(grunt);
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.initConfig({
        less: {
            development: {
                options: {
                    compress: true,
                    yuicompress: true,
                    optimization: 2
                },
                files: {
                    "lcc/static/css/main.css": "lcc/src/less/main.less"
                }
            }
        },
        concat: {
            scripts: {
                src: [
                    'lcc/src/js/lib/jquery.min.js',
                    'lcc/src/js/lib/bootstrap.min.js',
                    'lcc/src/js/lib/tether.min.js',
                    'lcc/src/js/common.js'
                ],
                dest: 'lcc/static/js/main.js'
            }
        },
        copy: {
            img: {
                expand: true,
                cwd: 'lcc/src/img',
                src: '**',
                dest: 'lcc/static/img/'
            },
            fonts: {
                expand: true,
                cwd: 'lcc/src/fonts',
                src: '**',
                dest: 'lcc/static/fonts'
            },
            js: {
                expand: true,
                cwd: 'lcc/src/js',
                src: '*.js',
                dest: 'lcc/static/js/'
            }
        },
        watch: {
            styles: {
                files: ['lcc/src/less/**/*.less'], // which files to watch
                tasks: ['less'],
                options: {
                    nospawn: true
                }
            },
            scripts: {
                files: ['lcc/src/js/**/*.js'],
                tasks: ['concat', 'copy'],
                options: {
                    nospawn: true
                }
            }
        },
        uglify: {
            my_target: {
                files: {
                    'lcc/static/*/*.js': ['lcc/static/*/*.js']
                }
            }
        }
    });

    grunt.registerTask('default', ['less', 'concat', 'copy']);
    grunt.registerTask('dev', ['less', 'concat', 'copy', 'watch']);
    grunt.registerTask('prod', ['less', 'concat', 'copy', 'uglify']);


};
